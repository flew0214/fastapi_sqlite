"""
数据库管理工具：聊天室频道和消息管理

功能：
1. 查看各频道的消息统计
2. 真实删除消息（永久删除）
3. 查看所有频道列表
4. 按频道过滤消息
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "chat.db"

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_FILE)

def show_all_channels():
    """显示所有频道及其消息统计"""
    conn = get_connection()
    try:
        query = """
            SELECT
                channel,
                COUNT(*) as message_count,
                COUNT(DISTINCT user_id) as unique_users,
                MIN(created_at) as first_message,
                MAX(created_at) as last_message
            FROM messages
            WHERE is_deleted = 0
            GROUP BY channel
            ORDER BY message_count DESC
        """
        df = pd.read_sql_query(query, conn)
        print("\n" + "="*80)
        print("📊 频道统计")
        print("="*80)
        if df.empty:
            print("暂无消息")
        else:
            print(df.to_string(index=False))
        return df
    finally:
        conn.close()

def show_messages(channel=None, limit=20, include_deleted=False):
    """显示消息（可按频道过滤）"""
    conn = get_connection()
    try:
        if channel:
            where_clause = f"WHERE channel = '{channel}'"
        else:
            where_clause = ""

        if not include_deleted:
            if where_clause:
                where_clause += " AND is_deleted = 0"
            else:
                where_clause = "WHERE is_deleted = 0"

        query = f"""
            SELECT
                m.id,
                u.username,
                m.content,
                m.channel,
                CASE WHEN m.is_deleted = 1 THEN '✗ 已删除' ELSE '✓ 正常' END as status,
                m.created_at
            FROM messages m
            LEFT JOIN users u ON m.user_id = u.id
            {where_clause}
            ORDER BY m.created_at DESC
            LIMIT {limit}
        """
        df = pd.read_sql_query(query, conn)
        print("\n" + "="*120)
        title = f"📝 消息列表" + (f" [频道: {channel}]" if channel else "")
        print(title)
        print("="*120)
        if df.empty:
            print("暂无消息")
        else:
            for idx, row in df.iterrows():
                print(f"\nID: {row['id']} | 用户: {row['username']} | 频道: {row['channel']} | 状态: {row['status']}")
                print(f"内容: {row['content']}")
                print(f"时间: {row['created_at']}")
        return df
    finally:
        conn.close()

def force_delete_messages(channel=None, confirm=True):
    """真实（强制）删除消息"""
    conn = get_connection()
    try:
        if channel:
            query = f"SELECT COUNT(*) FROM messages WHERE channel = '{channel}'"
            delete_query = f"DELETE FROM messages WHERE channel = '{channel}'"
            msg_type = f"频道 '{channel}' 中的所有 "
        else:
            query = "SELECT COUNT(*) FROM messages"
            delete_query = "DELETE FROM messages"
            msg_type = "数据库中所有 "

        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]

        if count == 0:
            print("没有需要删除的消息")
            return False

        print(f"\n⚠️  即将真实删除 {count} 条{msg_type}消息")
        print("此操作不可恢复！")

        if confirm:
            confirm_input = input("\n确认删除？(输入 YES 继续): ")
            if confirm_input != "YES":
                print("取消删除")
                return False

        cursor.execute(delete_query)
        conn.commit()
        print(f"✅ 成功删除 {count} 条{msg_type}消息")
        return True
    finally:
        conn.close()

def soft_delete_all(channel=None):
    """软删除所有消息（标记删除）"""
    conn = get_connection()
    try:
        if channel:
            query = f"UPDATE messages SET is_deleted = 1 WHERE channel = '{channel}' AND is_deleted = 0"
            msg_type = f"频道 '{channel}' 中所有未删除的"
        else:
            query = "UPDATE messages SET is_deleted = 1 WHERE is_deleted = 0"
            msg_type = "所有未删除的"

        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.rowcount
        conn.commit()
        print(f"✅ 已将 {count} 条{msg_type}消息标记为已删除")
        return count
    finally:
        conn.close()

def main():
    """主菜单"""
    while True:
        print("\n" + "="*80)
        print("🗄️  聊天室数据库管理工具")
        print("="*80)
        print("1. 查看所有频道统计")
        print("2. 查看消息（所有频道）")
        print("3. 查看消息（指定频道）")
        print("4. 查看消息（包括已删除的）")
        print("5. 软删除所有消息（标记删除）")
        print("6. 软删除指定频道消息")
        print("7. 真实删除所有消息（永久删除）")
        print("8. 真实删除指定频道消息")
        print("0. 退出")

        choice = input("\n请选择操作 (0-8): ").strip()

        if choice == "1":
            show_all_channels()

        elif choice == "2":
            limit = input("显示条数 (默认20): ").strip()
            show_messages(limit=int(limit) if limit else 20)

        elif choice == "3":
            channel = input("请输入频道名称 (默认default): ").strip() or "default"
            limit = input("显示条数 (默认20): ").strip()
            show_messages(channel=channel, limit=int(limit) if limit else 20)

        elif choice == "4":
            channel = input("请输入频道名称 (空=所有频道): ").strip() or None
            limit = input("显示条数 (默认20): ").strip()
            show_messages(channel=channel, limit=int(limit) if limit else 20, include_deleted=True)

        elif choice == "5":
            soft_delete_all()

        elif choice == "6":
            channel = input("请输入频道名称 (默认default): ").strip() or "default"
            soft_delete_all(channel)

        elif choice == "7":
            confirm = input("是否需要确认？(Y/n): ").strip().lower() != 'n'
            force_delete_messages(confirm=confirm)

        elif choice == "8":
            channel = input("请输入频道名称 (默认default): ").strip() or "default"
            confirm = input("是否需要确认？(Y/n): ").strip().lower() != 'n'
            force_delete_messages(channel=channel, confirm=confirm)

        elif choice == "0":
            print("再见！")
            break

        else:
            print("无效选择,请重新输入")

if __name__ == "__main__":
    main()
