from app.configs.model_config import Gemini
from app.prompts.base_prompt import BasePrompt
from app.models.state import State
from app.exceptions.chat_exception import InvalidInputException, ModelNotFoundException, ToolExecutionException
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from app.workflow.tools.chat_tools import Chat
from app.constants.define_order  import DefineOrder
from app.database import PineconeDatabase, PostgresDatabase
from app.models.message import MessageRole
from app.models import ChatMessage
import re
import json
import ast

class RouteNode:
    def __init__(self):
        try:
            self._gemini = Gemini()
            self._llm = self._gemini.llm()
            self._prompt = BasePrompt()
            self._chat = Chat()
            self._llm_bind_tools = self._chat.get_llm_binds_tools()
            self._tool_node = self._chat.get_tool_node()
            self._vector_store = PineconeDatabase().connect()
            self._postgres = PostgresDatabase()
            self._define_order = DefineOrder()
        except Exception as e:
            raise ModelNotFoundException(f"Failed to initialize chat models: {str(e)}")

    @staticmethod
    def _ai_to_json(ai: AIMessage):
        if hasattr(ai, "content"):
            content = ai.content
        elif isinstance(ai, str):
            content = ai
        else:
            raise InvalidInputException("Invalid AI message format")

        content = re.sub(r"^```json\n|```$", "", content.strip(), flags=re.MULTILINE)
        
        print("AI Content:", content)

        try:
            cleaned = content.strip().lstrip('{').rstrip('}')
            json_data = json.loads('{' + cleaned + '}')
            return json_data
        except json.JSONDecodeError as e:
            raise InvalidInputException(f"Failed to parse AI response as JSON: {str(e)}")
    
    @staticmethod
    def str_to_list_of_str(data_str):
        data = ast.literal_eval(data_str)
        return [str(item) for item in data]

    def route(self, state: State):
        messages = state.user_input

        decision = self._llm.invoke([
            SystemMessage(content=self._prompt.route_instructions),
            HumanMessage(content=messages),
        ])
        state.next_state = self._ai_to_json(decision).get("datasource")
        # print("Decision:", state["next_state"])

        # state["next_state"] = "tools" if decision.get("datasource") == "tools" else "generate"
        return state
    
    def using_tools(self, state: State):
        messages = state.user_input

        tool_prompt = self._prompt.using_tools_prompt.format(
            user_id=state.user_id,
            user_input=messages
        )

        if not messages or not isinstance(messages, str) or messages.strip() == "":
            raise ValueError("User input is empty or invalid. Please provide a valid input.")

        result = self._llm_bind_tools.invoke([
            SystemMessage(content=tool_prompt),
            HumanMessage(content=messages),
        ])


        tool_call = result.tool_calls[0]
        tool_call['args']['state']['user_input'] = messages

        ai_msg = AIMessage(
            content=result.content,
            additional_kwargs=result.additional_kwargs,
            tool_calls=[tool_call]
        )

        if result.tool_calls:
            # state = 
            final_result = self._tool_node.invoke([ai_msg])
            print("Tool Result:", final_result)

            match tool_call['name']:
                case "search_paintings_by_keyword":
                    convert_prompt = self._prompt.search_paintings_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )
                case "order_painting":
                    convert_prompt = self._prompt.order_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )
                case "get_size_available":
                    convert_prompt = self._prompt.size_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )
                case "get_category_available":
                    convert_prompt = self._prompt.category_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )
                case "get_coupon_available":
                    convert_prompt = self._prompt.coupon_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )
                case _:
                    convert_prompt = self._prompt.default_prompt.format(
                        tool_run=final_result,
                        question=messages,
                    )


            generation = self._llm.invoke([
                SystemMessage(content=convert_prompt),
                *state.chat_history,
                HumanMessage(content=messages),
            ])
            
            state.final_generation = generation.content
   
            state.chat_history.append(HumanMessage(content=messages))
            state.chat_history.append(generation)

            if state.user_id and state.user_id.strip():
                # chỉ khi user_id không None, không rỗng, không toàn khoảng trắng
                chat_message_user = ChatMessage(
                    user_id=state.user_id,
                    role=MessageRole.USER,
                    content=messages
                )
                self._postgres.save_message(chat_message_user)

                chat_message_ai = ChatMessage(
                    user_id=state.user_id,
                    role=MessageRole.AI,
                    content=state.final_generation
                )
                self._postgres.save_message(chat_message_ai)
            
        state.next_state = "end"

        return state
    
    def generate(self, state: State):
        messages = state.user_input
        

        self.similarity_search(state)

        prompt_generation = self._prompt.generate_prompt.format(
            question=messages,
            context=state.context,
            history=[],
        )


        generation = self._llm.invoke([
            SystemMessage(content=prompt_generation),
            *state.chat_history,
            HumanMessage(content=messages),
        ])

        state.final_generation = generation.content if isinstance(generation, AIMessage) else generation

        state.chat_history.append(HumanMessage(content=messages))
        state.chat_history.append(generation)

        if state.user_id and state.user_id.strip():
            # chỉ khi user_id không None, không rỗng, không toàn khoảng trắng
            chat_message_user = ChatMessage(
                user_id=state.user_id,
                role=MessageRole.USER,
                content=messages
            )
            self._postgres.save_message(chat_message_user)

            chat_message_ai = ChatMessage(
                user_id=state.user_id,
                role=MessageRole.AI,
                content=state.final_generation
            )
            self._postgres.save_message(chat_message_ai)
        

        return state
    
    def order(self, state: State):
        messages = state.user_input

        self.similarity_search(state)

        order_instructions = self._prompt.order_instructions.format(
            history=state.chat_history,
            context=state.context,
            payment_methods=self._define_order.payment_methods,
            shipping_policy=self._define_order.shipping_policy,
            delivery_info=self._define_order.delivery_info,
            order_steps=self._define_order.order_steps,
        )


        generation = self._llm.invoke([
            SystemMessage(content=order_instructions),
            *state.chat_history,
            HumanMessage(content=messages),
        ])

        state.final_generation = generation.content if isinstance(generation, AIMessage) else generation
        state.chat_history.append(HumanMessage(content=messages))
        state.chat_history.append(generation)


        if state.user_id and state.user_id.strip():
                # chỉ khi user_id không None, không rỗng, không toàn khoảng trắng
            chat_message_user = ChatMessage(
                user_id=state.user_id,
                role=MessageRole.USER,
                content=messages
            )
            self._postgres.save_message(chat_message_user)

            chat_message_ai = ChatMessage(
                user_id=state.user_id,
                role=MessageRole.AI,
                content=state.final_generation
            )
            self._postgres.save_message(chat_message_ai)

        return state

    def similarity_search(self, state: State):
        """
        Tìm kiếm với keyword filtering để tăng hiệu quả (áp dụng cho Pinecone).
        """

        docs = self._vector_store.similarity_search(
            query=state.user_input,
            k=3
        )

        context = "\n".join([doc.page_content for doc in docs])
        state.context = context
        return state
    
    # def clarify_detector(self, state: State):
    #     """
    #     Phát hiện câu hỏi cần làm rõ và trả về thông tin cần thiết.
    #     """
    #     messages = state.user_input

    #     clarify_prompt = self._prompt.clarify_prompt.format(
    #         question=messages,
    #         context=state.context,
    #         history=[],
    #     )

    #     generation = self._llm.invoke([
    #         SystemMessage(content=clarify_prompt),
    #         *state.chat_history,
    #         HumanMessage(content=messages),
    #     ])

    #     state.final_generation = generation.content if isinstance(generation, AIMessage) else generation
    #     state.chat_history.append(HumanMessage(content=messages))
    #     state.chat_history.append(generation)

    #     return state    