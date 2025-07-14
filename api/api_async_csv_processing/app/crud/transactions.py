

async def get_transaction_details(transaction_id: str, cursor=None) -> dict:
    query = f"""
    SELECT * FROM transactions WHERE id = %s
    """
    await cursor.execute(query, (transaction_id,))
    transaction = await cursor.fetchone()

    if not transaction:
        return {}

    return {
        "id": transaction[0],
        "user_id": transaction[1],
        "amount": transaction[2],
        "currency": transaction[3],
        "status": transaction[4],
        "created_at": transaction[5]
    }
