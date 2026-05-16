def make_chain(prompt_fn, client):
    return lambda payload: client.answer(
        payload["question"], payload.get("context", ""), prompt_fn()
    )
