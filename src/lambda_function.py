import os
import datetime
import psycopg2
import json

def lambda_handler(event, context):
    print("Event:", event)
    print("Raw body:", event.get("body"))
    db_name = os.environ['DB_NAME']
    db_host = os.environ['DB_HOST']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', 5432)

    today = datetime.date.today()
    current_month = today.month
    current_year = today.year

    # リクエストボディを取得
    # json.loads() は JSON文字列(例:HTTPリクエスト本文から：'body': '{"mode":"all"}')を「Pythonが扱えるデータ構造」変換するための魔法の変換関数
    body = json.loads(event.get("body", "{}"))
    mode = body.get("mode")

    try:
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        cur = conn.cursor()

        rows = []

        # --- mode 分岐 ---
        if mode == "all":
            cur.execute("""
                SELECT id, user_id, title, description, start_time, end_time, location, category, is_all_day
                FROM calendar_events
                ORDER BY start_time;
            """)
            rows = cur.fetchall()

        elif mode == "by_user":
            user_id = body.get("user_id")
            if not user_id:
                return {"statusCode": 400, "body": json.dumps({"error": "user_id is required"})}
            cur.execute("""
                SELECT id, user_id, title, description, start_time, end_time, location, category, is_all_day
                FROM calendar_events
                WHERE user_id = %s
                ORDER BY start_time;
            """, (user_id,))
            rows = cur.fetchall()

        elif mode == "by_category":
            category = body.get("category")
            if not category:
                return {"statusCode": 400, "body": json.dumps({"error": "category is required"})}
            cur.execute("""
                SELECT id, user_id, title, description, start_time, end_time, location, category, is_all_day
                FROM calendar_events
                WHERE category = %s
                ORDER BY start_time;
            """, (category,))
            rows = cur.fetchall()

        elif mode == "by_date":
            from_date = body.get("from_date")
            to_date = body.get("to_date")
            if not from_date or not to_date:
                return {"statusCode": 400, "body": json.dumps({"error": "from_date and to_date are required (YYYY-MM-DD)"})}
            cur.execute("""
                SELECT id, user_id, title, description, start_time, end_time, location, category, is_all_day
                FROM calendar_events
                WHERE start_time >= %s AND start_time < %s
                ORDER BY start_time;
            """, (from_date, to_date))
            rows = cur.fetchall()

        else:
            # デフォルトは「今月分の予定」
            cur.execute("""
                SELECT id, user_id, title, description, start_time, end_time, location, category, is_all_day
                FROM calendar_events
                WHERE EXTRACT(MONTH FROM start_time) = %s
                  AND EXTRACT(YEAR FROM start_time) = %s
                ORDER BY start_time;
            """, (current_month, current_year))
            rows = cur.fetchall()

        # JSON変換
        events = [
            {
                "id": r[0],
                "user_id": r[1],
                "title": r[2],
                "description": r[3],
                "start_time": str(r[4]),
                "end_time": str(r[5]),
                "location": r[6],
                "category": r[7],
                "is_all_day": r[8]
            }
            for r in rows
        ]

        cur.close()
        conn.close()

        return {
            "statusCode": 200,
            "headers": {
            "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
            "Access-Control-Allow-Headers": "Content-Type",
             "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps(events, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
            "Access-Control-Allow-Origin": "http://127.0.0.1:5500",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
             },
            "body": json.dumps({"error": str(e)})
        }
