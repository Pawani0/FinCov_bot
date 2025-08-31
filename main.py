from fastapi import FastAPI, WebSocket, Query, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from query_engine.rag_pipeline import load_all_vectorstores, ask
from query_engine.classifier_engine import classify_domain, classify_intent
from utils.tts import stream_tts
from utils.chat_storage import dump_session_to_mongo, store_message 
from utils.auth_routes import router as auth_router
import json
from utils.user_data import extract_user_data
from utils.sessions import active_session, create_session, delete_session


with open("query_engine/intents.json", "r", encoding="utf-8") as file:
    all_intents = json.load(file)

app = FastAPI()
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vectorstores = load_all_vectorstores()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket, sid=Query(None)): 
    
    session_id = create_session()
        
    await websocket.accept()

    try:
        while True:
            raw_data = await websocket.receive_text()

            # Handle verification complete message
            session_info = active_session[session_id]
            if not session_info.get("is_verified", False):
                try:
                    parsed = json.loads(raw_data)
                    if isinstance(parsed, dict) and parsed.get("type") == "verification_complete":
                        session_info["is_verified"] = True
                        await websocket.send_json({
                            "type": "verified",
                            "message": "OTP verification successful"
                        })
                        continue
                    else:
                        query = raw_data
                except json.JSONDecodeError:
                    query = raw_data
            else:
                # If already verified, skip parsing overhead
                query = raw_data

            print(f"[User]: {query}")

            domain = classify_domain(query)
            print(f"[Domain]: {domain}")

            intent = classify_intent(query, domain)
            print(f"[Intent]: {intent}")

            # If intent needs OTP and session not verified
            if intent and not session_info.get("is_verified", False):
                await websocket.send_json({
                    "type": "auth_required",
                    "message": f"OTP verification is required for intent '{intent}'",
                    "intent": intent,
                    "SID": session_id
                })
                continue
                
            if not domain:
                response = ask(session_id, query, vectorstores["banking"])
            else:
                if intent:
                    # response = all_intents.get(domain, {}).get(intent)
                    # if not response:
                    #     response = ask(session_id, query, vectorstores[domain])
                    print("[phone]: ", session_info["phone_number"])
                    if not session_info["user_data"]:
                        session_info["user_data"] = extract_user_data(session_info["phone_number"])
                    print(f"[user_data]: {session_info['user_data']}")
                    response = ask(session_id, query, vectorstores[domain], session_info["user_data"])
                else:
                    response = ask(session_id, query, vectorstores[domain])

            print(f"[Maya]: {response}")

            # Send text response
            await websocket.send_text(json.dumps({"type": "text", "data": response}))

            # Stream TTS
            async for chunk in stream_tts(response):
                await websocket.send_bytes(chunk)

            store_message(session_id, query, response, domain, intent)

    except WebSocketDisconnect:
        if session_id in active_session:
            dump_session_to_mongo(session_id)
            delete_session(session_id)
        print(f"WebSocket disconnected for session {session_id}")

    except Exception as e:
        print(f"Error in session {session_id}:", e)
        if session_id in active_session:
            dump_session_to_mongo(session_id)
            delete_session(session_id)
