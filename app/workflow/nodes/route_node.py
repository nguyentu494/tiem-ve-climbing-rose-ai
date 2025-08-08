from app.configs.model_config import Gemini
from app.prompts.base_prompt import BasePrompt
from app.models.state import State
from app.exceptions.chat_exception import (
    InvalidInputException,
    ModelNotFoundException,
)
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from app.workflow.tools.chat_tools import Chat
from app.constants.define_order import DefineOrder
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
        return [str(item) for item in ast.literal_eval(data_str)]

    def similarity_search(self, state: State):
        docs = self._vector_store.similarity_search(
            query=state.user_input,
            k=3
        )
        state.context = "\n".join([doc.page_content for doc in docs])
        return state

    def route(self, state: State):
        decision = self._llm.invoke([
            SystemMessage(content=self._prompt.route_instructions),
            HumanMessage(content=state.user_input),
        ])
        state.next_state = self._ai_to_json(decision).get("datasource")
        return state

    def evaluate_history(self, state: State):
        

        prompt = self._prompt.evaluate_history.format(
            user_input=state.user_input,
            history=state.context,
        )

        decision = self._llm.invoke([
            SystemMessage(content=prompt),
            *state.chat_history,  
            HumanMessage(content=state.user_input),
        ])

        try:
            result = self._ai_to_json(decision)
        except InvalidInputException:
            result = None

        if not result or not isinstance(result, dict):
            state.final_generation = decision.content
            state.next_state = "end"
            return state

        state.next_state = "generate" if result.get("datasource") in [True, "true"] else "route"
        return state


    def using_tools(self, state: State):
        if not state.user_input or not isinstance(state.user_input, str) or not state.user_input.strip():
            raise ValueError("User input is empty or invalid. Please provide a valid input.")

        tool_prompt = self._prompt.using_tools_prompt.format(
            user_id=state.user_id,
            user_input=state.user_input
        )

        result = self._llm_bind_tools.invoke([
            SystemMessage(content=tool_prompt),
            HumanMessage(content=state.user_input),
        ])

        if not result.tool_calls or len(result.tool_calls) == 0:
            raise InvalidInputException("No tool calls found in the AI response. Please check the input or model configuration.")
        tool_call = result.tool_calls[0]
        tool_call['args']['state']['user_input'] = state.user_input

        ai_msg = AIMessage(
            content=result.content,
            additional_kwargs=result.additional_kwargs,
            tool_calls=[tool_call]
        )

        final_result = self._tool_node.invoke([ai_msg])

        prompt_map = {
            "search_paintings_by_keyword": self._prompt.search_paintings_prompt,
            "order_painting": self._prompt.order_prompt,
            "get_size_available": self._prompt.size_prompt,
            "get_category_available": self._prompt.category_prompt,
            "get_coupon_available": self._prompt.coupon_prompt,
        }

        prompt_template = prompt_map.get(tool_call['name'], self._prompt.generate_prompt)

        convert_prompt = prompt_template.format(
            tool_run=final_result,
            question=state.user_input
        )

        generation = self._llm.invoke([
            SystemMessage(content=convert_prompt),
            *state.chat_history,
            HumanMessage(content=state.user_input),
        ])

        state.final_generation = generation.content
        state.chat_history += [HumanMessage(content=state.user_input), generation]
        self._save_chat(state)
        state.next_state = "end"
        return state

    def generate(self, state: State):
        self.similarity_search(state)

        prompt = self._prompt.generate_prompt.format(
            question=state.user_input,
            context=state.context,
            history=[]
        )

        generation = self._llm.invoke([
            SystemMessage(content=prompt),
            *state.chat_history,
            HumanMessage(content=state.user_input),
        ])

        state.final_generation = generation.content
        state.chat_history += [HumanMessage(content=state.user_input), generation]
        self._save_chat(state)
        return state

    def order(self, state: State):
        self.similarity_search(state)

        prompt = self._prompt.order_instructions.format(
            history=state.chat_history,
            context=state.context,
            payment_methods=self._define_order.payment_methods,
            shipping_policy=self._define_order.shipping_policy,
            delivery_info=self._define_order.delivery_info,
            order_steps=self._define_order.order_steps,
        )

        generation = self._llm.invoke([
            SystemMessage(content=prompt),
            *state.chat_history,
            HumanMessage(content=state.user_input),
        ])

        state.final_generation = generation.content
        state.chat_history += [HumanMessage(content=state.user_input), generation]
        self._save_chat(state)
        return state

    def _save_chat(self, state: State):
        if not state.user_id or not state.user_id.strip():
            return

        self._postgres.save_message(ChatMessage(
            user_id=state.user_id,
            role=MessageRole.USER,
            content=state.user_input
        ))

        self._postgres.save_message(ChatMessage(
            user_id=state.user_id,
            role=MessageRole.AI,
            content=state.final_generation
        ))
