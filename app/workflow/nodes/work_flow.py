from app.workflow.nodes.route_node import RouteNode
from langgraph.graph import StateGraph, END
from app.models.state import State
from langgraph.checkpoint.memory import MemorySaver
from app.models.extract_param import SearchParams
from app.models.chat_request import ChatRequest
from app.database import RedisDatabase 

class FlowGraph:
    def __init__(self):
        self._redis_db = RedisDatabase()
        self._checkpointer = self._redis_db.connect()
        self._max_rounds = 4
        
        nodes = RouteNode()
        graph_builder = StateGraph(state_schema=State)
    
        # Add các node
        # graph_builder.add_node("evaluate_history", nodes.evaluate_history)
        # graph_builder.add_node("summarize_history", nodes.summarize_history)
        # graph_builder.add_node("check_relevant", nodes.is_context_relevant)
        # graph_builder.add_node("route", nodes.route)
        # graph_builder.add_node("tools", nodes.using_tools)
        # graph_builder.add_node("order", nodes.order)
        graph_builder.add_node("generate", nodes.generate)

        # Set entry point
        # graph_builder.set_entry_point("evaluate_history") 
        # graph_builder.add_conditional_edges(
        #     "evaluate_history",
        #     lambda state: state.next_state,
        #     {
        #         "summarize_history": "summarize_history",
        #         "generate": "generate",
        #         "end": END  
        #     }
        # )

        # graph_builder.add_edge("summarize_history", "check_relevant")
        # graph_builder.add_edge("check_relevant", "route")

        # # Định nghĩa các conditional edges từ router
        # graph_builder.add_conditional_edges(
        #     "route",
        #     lambda state: state.next_state,
        #     {
        #         "tools": "tools",
        #         "order": "order",
        #         "generate": "generate"
        #     }
        # )

        # # Định nghĩa các edges khác không liên quan đến router
        # graph_builder.add_edge("tools", END)
        # graph_builder.add_edge("order", END)
        graph_builder.add_edge("generate", END)

        # self._graph = graph_builder.compile(checkpointer=self._checkpointer)

        self._graph = graph_builder.compile()

    def __close__(self):
        self._redis_db.close()


    def get_graph(self):
        return self._graph.get_graph().draw_mermaid()

    def run(self, chat_request: ChatRequest):

        thread_id = {
            "configurable": {
                "thread_id": chat_request.user_id,
            }
        }
        # state.chat_history = 
        try:
            saved_chat_history = self._checkpointer.get(thread_id) or {}
        except Exception as e:
            print("⚠️ Không lấy được checkpoint:", e)
            saved_chat_history = {}       
        channel_values = saved_chat_history.get("channel_values", {})
        history = channel_values.get("chat_history", [])

        if history:
            history_trimmed = history[-(self._max_rounds*2):] if len(history) > self._max_rounds else history
        else:
            history_trimmed = []

        
        initial_state = State(
            chat_id=chat_request.chat_id,
            user_input=chat_request.user_input,
            chat_history=history_trimmed,
            generation="",
            final_generation="",
            context=[],
            error=[],
            next_state="route",
            is_relevant=True,
            loop_step=0,
            user_id=chat_request.user_id,
            search_params=SearchParams(
                keyword=None,
                max_price=None,
                size=None,
                painting_id=None
            )
        )

        result = self._graph.invoke(initial_state, config=thread_id)

        return result['final_generation']

if __name__ == "__main__":
    flow_graph = FlowGraph()
    # Example run
    result = flow_graph.run("Tìm tranh cô gái")
