import sqlite3
from app.database import conn
from fastapi import APIRouter, HTTPException
from app.models import ItemCreate

router = APIRouter(prefix="/items", tags=["items"])


def get_cursor():
    return conn.cursor()


@router.post("/", status_code=201)
def create_item(item: ItemCreate):
    try:
        cursor = get_cursor()
        cursor.execute("INSERT INTO items (id, name) VALUES (?, ?)", (item.id, item.name))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Item already exists")
    return item


@router.get("/{item_id}")
def read_item(item_id: int):
    cursor = get_cursor()
    cursor.execute("SELECT id, name FROM items WHERE id=?", (item_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "Item not found")
    return {"id": row[0], "name": row[1]}


@router.get("/")
def read_all_items():
    cursor = get_cursor()
    cursor.execute("SELECT id, name FROM items")
    rows = cursor.fetchall()
    # Converts tuples -> dicts
    items_list = [{"id": r[0], "name": r[1]} for r in rows]
    return items_list


@router.put("/{item_id}")
def update_item(item_id: int, name: str):
    cursor = get_cursor()
    cursor.execute("UPDATE items Set name=? WHERE id=?", (name, item_id))
    if cursor.rowcount == 0:
        raise HTTPException(404, "Item not found")
    conn.commit()
    return {"id": item_id, "name": name}


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int):
    cursor = get_cursor()
    cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
    if cursor.rowcount == 0:
        raise HTTPException(404, "Item not found")
    conn.commit()
    return
