import streamlit as st
import psycopg2
import pandas as pd
import datetime
import re

from google import genai


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.title("🎓 Student Registration")

st.image(
    "images/PROFILE.jpeg",
    width=300
)


# =========================================================
# LOAD AI PROMPT
# =========================================================

def load_sql_prompt():

    with open(
        "prompts/sql_prompt.txt",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# =========================================================
# POSTGRESQL CONNECTION
# =========================================================

def get_connection():

    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"]
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

gemini_client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# =========================================================
# STUDENT REGISTRATION FORM
# =========================================================

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


# =========================================================
# INSERT STUDENT DATA
# =========================================================

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
            (
                name,
                email,
                phone,
                course,
                dob
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        st.success(
            "✅ Student information submitted successfully!"
        )

    except Exception as e:

        st.error("❌ Database Error")
        st.error(e)


# =========================================================
# DISPLAY STUDENTS
# =========================================================

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

    columns = [
        description[0]
        for description in cursor.description
    ]

    df = pd.DataFrame(
        records,
        columns=columns
    )

    st.subheader("📋 Student Records")

    st.dataframe(
        df,
        use_container_width=True
    )

    cursor.close()
    conn.close()

except Exception as e:

    st.error(
        "❌ Could not load student records"
    )

    st.error(e)


# =========================================================
# AI DATABASE ASSISTANT
# =========================================================

st.divider()

st.header("🤖 AI Database Assistant")

st.write(
    "Ask a question about the student database "
    "using normal English."
)


# =========================================================
# USER QUESTION
# =========================================================

user_prompt = st.text_area(
    "Ask your question",

    placeholder=(
        "Example:\n"
        "Give me month-wise student registration count\n\n"
        "or\n\n"
        "Give me the list of students who registered "
        "in September 2026"
    ),

    height=120
)


# =========================================================
# GENERATE SQL
# =========================================================

if st.button("🧠 Generate SQL"):

    if not user_prompt.strip():

        st.warning(
            "⚠️ Please enter a question first."
        )

    else:

        try:

            # Load prompt from external file
            system_prompt = load_sql_prompt()


            # Send prompt + user question to Gemini
            with st.spinner(
                "🤖 Gemini is generating SQL..."
            ):

                response = (
                    gemini_client.models.generate_content(
                        model="gemini-3.8-flash",

                        contents=(
                            system_prompt
                            + "\n\nUSER QUESTION:\n"
                            + user_prompt
                        )
                    )
                )


            # Get Gemini response
            generated_sql = response.text.strip()


            # =================================================
            # CLEAN MARKDOWN CODE FENCES
            # =================================================

            generated_sql = re.sub(
                r"^```sql\s*",
                "",
                generated_sql,
                flags=re.IGNORECASE
            )

            generated_sql = re.sub(
                r"^```\s*",
                "",
                generated_sql
            )

            generated_sql = re.sub(
                r"\s*```$",
                "",
                generated_sql
            )

            generated_sql = generated_sql.strip()


            # =================================================
            # STORE SQL IN SESSION STATE
            # =================================================

            st.session_state[
                "generated_sql"
            ] = generated_sql


            st.success(
                "✅ SQL generated successfully!"
            )


        except Exception as e:

            st.error(
                "❌ Gemini API Error"
            )

            st.error(e)


# =========================================================
# DISPLAY GENERATED SQL
# =========================================================

if "generated_sql" in st.session_state:

    st.subheader("🔍 Generated SQL")

    st.code(
        st.session_state["generated_sql"],
        language="sql"
    )


    # =====================================================
    # EXECUTE SQL
    # =====================================================

    if st.button("▶️ Execute SQL"):

        sql = (
            st.session_state["generated_sql"]
            .strip()
        )

        sql_upper = sql.upper().strip()


        # =================================================
        # SQL SAFETY VALIDATION
        # =================================================

        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):

            st.error(
                "🚫 Only SELECT queries are allowed."
            )


        # Block multiple SQL statements
        elif ";" in sql[:-1]:

            st.error(
                "🚫 Multiple SQL statements are not allowed."
            )


        else:

            forbidden_keywords = [
                "INSERT",
                "UPDATE",
                "DELETE",
                "DROP",
                "ALTER",
                "TRUNCATE",
                "CREATE",
                "GRANT",
                "REVOKE"
            ]


            unsafe_query = False


            for keyword in forbidden_keywords:

                if re.search(
                    rf"\b{keyword}\b",
                    sql_upper
                ):

                    unsafe_query = True

                    break


            if unsafe_query:

                st.error(
                    "🚫 Unsafe SQL query detected."
                )


            else:

                try:

                    # =================================================
                    # EXECUTE QUERY
                    # =================================================

                    with st.spinner(
                        "🗄️ Executing query..."
                    ):

                        conn = get_connection()

                        result_df = pd.read_sql_query(
                            sql,
                            conn
                        )

                        conn.close()


                    # =================================================
                    # DISPLAY RESULT
                    # =================================================

                    st.success(
                        "✅ Query executed successfully!"
                    )

                    st.subheader(
                        "📊 Query Result"
                    )

                    st.dataframe(
                        result_df,
                        use_container_width=True
                    )

                    st.caption(
                        f"Rows returned: {len(result_df)}"
                    )


                except Exception as e:

                    st.error(
                        "❌ SQL Execution Error"
                    )

                    st.error(e)

