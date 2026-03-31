from pathlib import Path

from flask import Flask, render_template

from db import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)


def fetch_one_dict(cursor, query):
    cursor.execute(query)
    columns = [column[0].lower() for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return {}
    return dict(zip(columns, row))


def fetch_all_dicts(cursor, query):
    cursor.execute(query)
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@app.route("/")
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    overview = fetch_one_dict(
        cursor,
        """
        SELECT
            COUNT(*) AS employees_count,
            COUNT(DISTINCT role) AS roles_count,
            NVL(SUM(salary), 0) AS total_salary,
            NVL(ROUND(AVG(salary), 2), 0) AS average_salary,
            NVL(MAX(salary), 0) AS max_salary
        FROM employees
        """,
    )

    ticket_stats = fetch_one_dict(
        cursor,
        """
        SELECT
            COUNT(*) AS tickets_count,
            SUM(CASE WHEN UPPER(status) = 'OPEN' THEN 1 ELSE 0 END) AS open_tickets,
            SUM(CASE WHEN UPPER(status) <> 'OPEN' THEN 1 ELSE 0 END) AS closed_tickets
        FROM tickets
        """,
    )

    role_breakdown = fetch_all_dicts(
        cursor,
        """
        SELECT
            role,
            COUNT(*) AS employee_count,
            ROUND(AVG(salary), 2) AS average_salary
        FROM employees
        GROUP BY role
        ORDER BY employee_count DESC, average_salary DESC
        """,
    )

    team_workload = fetch_all_dicts(
        cursor,
        """
        SELECT
            e.name,
            e.role,
            COUNT(t.id) AS ticket_count,
            SUM(CASE WHEN UPPER(t.status) = 'OPEN' THEN 1 ELSE 0 END) AS open_ticket_count
        FROM employees e
        LEFT JOIN tickets t ON t.employee_id = e.id
        GROUP BY e.name, e.role
        ORDER BY ticket_count DESC, open_ticket_count DESC, e.name
        """,
    )

    recent_tickets = fetch_all_dicts(
        cursor,
        """
        SELECT *
        FROM (
            SELECT
                t.id,
                t.title,
                t.status,
                e.name AS employee_name
            FROM tickets t
            LEFT JOIN employees e ON e.id = t.employee_id
            ORDER BY t.id DESC
        )
        WHERE ROWNUM <= 5
        """,
    )

    return render_template(
        "dashboard.html",
        overview=overview,
        ticket_stats=ticket_stats,
        role_breakdown=role_breakdown,
        team_workload=team_workload,
        recent_tickets=recent_tickets,
    )


@app.route("/employees")
def employees():
    conn = get_connection()
    cursor = conn.cursor()

    overview = fetch_one_dict(
        cursor,
        """
        SELECT
            COUNT(*) AS employees_count,
            COUNT(DISTINCT role) AS roles_count,
            NVL(SUM(salary), 0) AS total_salary,
            NVL(ROUND(AVG(salary), 2), 0) AS average_salary
        FROM employees
        """,
    )

    data = fetch_all_dicts(
        cursor,
        """
        SELECT
            e.id,
            e.name,
            e.role,
            e.salary,
            COUNT(t.id) AS ticket_count,
            SUM(CASE WHEN UPPER(t.status) = 'OPEN' THEN 1 ELSE 0 END) AS open_ticket_count
        FROM employees e
        LEFT JOIN tickets t ON t.employee_id = e.id
        GROUP BY e.id, e.name, e.role, e.salary
        ORDER BY e.salary DESC, e.name
        """,
    )

    top_employee = data[0] if data else None

    return render_template(
        "employees.html",
        overview=overview,
        employees=data,
        top_employee=top_employee,
    )


@app.route("/tickets")
def tickets():
    conn = get_connection()
    cursor = conn.cursor()

    ticket_stats = fetch_one_dict(
        cursor,
        """
        SELECT
            COUNT(*) AS tickets_count,
            SUM(CASE WHEN UPPER(status) = 'OPEN' THEN 1 ELSE 0 END) AS open_tickets,
            SUM(CASE WHEN UPPER(status) <> 'OPEN' THEN 1 ELSE 0 END) AS closed_tickets,
            SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END) AS unassigned_tickets
        FROM tickets
        """,
    )

    data = fetch_all_dicts(
        cursor,
        """
        SELECT
            t.id,
            t.title,
            t.status,
            t.employee_id,
            e.name AS employee_name,
            e.role AS employee_role
        FROM tickets t
        LEFT JOIN employees e ON e.id = t.employee_id
        ORDER BY
            CASE WHEN UPPER(t.status) = 'OPEN' THEN 0 ELSE 1 END,
            t.id DESC
        """,
    )

    return render_template(
        "tickets.html",
        ticket_stats=ticket_stats,
        tickets=data,
    )


if __name__ == "__main__":
    app.run(debug=True)
