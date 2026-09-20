import streamlit as st
import psycopg2
import pandas as pd
import datetime


st.title("🎓 Student Registration")


# -------------------------
# PostgreSQL connection
# -------------------------

def get_connection():

    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"]
    )


# -------------------------
# Student Form
# -------------------------

with st.form("student_form"):

    st.subheader("Enter Student Details")

    name = st.text_input("Name")

    email = st.text_input("Email")

    phone = st.text_input("Phone")

    course = st.text_input("Course")

    dob = st.date_input(
        "Date of Birth",
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.date.today()
    )

    submit = st.form_submit_button("Submit")


# -------------------------
# Insert Data
# -------------------------

if submit:

    try:

        conn = get_connection()

        cursor = conn.cursor()

        query = """
        INSERT INTO students
        (
            student_name,
            student_email,
            student_phone,
            student_course,
            student_dob
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (name, email, phone, course, dob)
        )

        conn.commit()

        cursor.close()
        conn.close()

        st.success("✅ Student information submitted successfully!")

    except Exception as e:

        st.error("❌ Database Error")
        st.error(e)


# -------------------------
# Display Students
# -------------------------

try:

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            student_id,
            student_name,
            student_email,
            student_phone,
            student_course,
            student_dob,
            created_at
        FROM students
        ORDER BY student_id DESC
    """)

    records = cursor.fetchall()

    columns = [description[0] for description in cursor.description]

    df = pd.DataFrame(records, columns=columns)

    st.subheader("📋 Student Records")

    st.dataframe(
        df,
        use_container_width=True
    )

    cursor.close()
    conn.close()

except Exception as e:

    st.error("❌ Could not load student records")
    st.error(e)

