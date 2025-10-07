import streamlit as st
import gspread
import pandas as pd
import json
import hashlib
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- 페이지 설정 ---
st.set_page_config(
    page_title="과학 실험 보고서 자동 생성",
    page_icon="🧪",
    layout="wide",
)

# --- 유틸리티 함수 ---
def hash_password(password):
    """비밀번호를 해시 처리하여 반환합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """제공된 비밀번호가 저장된 해시와 일치하는지 확인합니다."""
    return stored_hash == hash_password(provided_password)

# --- Google API 연결 함수 ---

def connect_to_gsheet():
    """Google Sheets에 연결하고 워크시트를 반환합니다."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet_url"])
        worksheet = spreadsheet.worksheet("학생 데이터")
        return worksheet
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {e}")
        return None

def get_google_api_service(service_name, version):
    """범용 Google API 서비스 빌더"""
    try:
        scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/documents"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return build(service_name, version, credentials=creds)
    except Exception as e:
        st.error(f"Google {service_name.capitalize()} API 연결 실패: {e}")
        return None

# --- 데이터 관리 함수 ---

def get_default_data():
    """새로운 학생을 위한 기본 데이터 구조를 반환합니다."""
    return {
        "title": "산-염기 적정 실험",
        "name": "",
        "password_hash": None,
        "doc_id": None,
        "measurements": pd.DataFrame({
            '시도': [1, 2, 3, '평균'],
            '사용한 염산(HCl) 용액의 부피(mL)': [10.0, 10.0, 10.0, 10.0],
            '소비된 수산화나트륨(NaOH) 용액의 부피(mL)': [0.0, 0.0, 0.0, 0.0]
        }).to_dict('records'),
        "analysis": "실험 결과에 대한 분석 내용을 여기에 작성하세요.",
        "conclusion": "결론 및 고찰 내용을 여기에 작성하세요."
    }

def load_student_data(worksheet, student_id):
    """특정 학생의 데이터를 Google Sheets에서 불러옵니다."""
    if worksheet is None: return None
    try:
        cell = worksheet.find(student_id)
        if cell:
            row_data = worksheet.row_values(cell.row)
            loaded_data = json.loads(row_data[1]) if len(row_data) > 1 else {}
            default_data = get_default_data()
            default_data.update(loaded_data)
            return default_data
        return get_default_data()
    except gspread.exceptions.CellNotFound:
        return get_default_data()
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return None

def save_student_data(worksheet, student_id, data):
    """학생 데이터를 Google Sheets에 저장합니다."""
    if worksheet is None: return
    try:
        # DataFrame을 to_dict('records')로 변환하여 저장
        if isinstance(data.get('measurements'), pd.DataFrame):
            data['measurements'] = data['measurements'].to_dict('records')
        
        data_json = json.dumps(data, ensure_ascii=False)
        cell = worksheet.find(student_id, in_column=1)
        if cell:
            worksheet.update_cell(cell.row, 2, data_json)
            st.toast("변경 사항이 저장되었습니다.", icon="💾")
        else:
            worksheet.append_row([student_id, data_json])
            st.toast("새로운 데이터가 저장되었습니다.", icon="💾")
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {e}")


# --- Google Docs 템플릿 처리 함수 ---

def create_doc_from_template(drive_service, template_id, title):
    """템플릿을 복사하여 새 Google Docs 문서를 생성합니다."""
    try:
        copied_file = {'name': title}
        new_doc = drive_service.files().copy(fileId=template_id, body=copied_file).execute()
        doc_id = new_doc.get('id')
        
        # 새 문서의 권한을 서비스 계정에 부여 (필요 시)
        permission = {'type': 'user', 'role': 'writer', 'emailAddress': st.secrets["gcp_service_account"]["client_email"]}
        drive_service.permissions().create(fileId=doc_id, body=permission).execute()
        
        return doc_id
    except Exception as e:
        st.error(f"템플릿 복사 중 오류 발생: {e}")
        st.warning("템플릿 문서가 서비스 계정에 '편집자'로 공유되었는지 확인하세요.")
        return None

def update_doc_with_data(docs_service, doc_id, report_data):
    """자리표시자를 실제 데이터로 교체하여 문서를 업데이트합니다."""
    try:
        # 1. 텍스트 자리표시자 교체
        df = pd.DataFrame(report_data['measurements'])
        # DataFrame을 텍스트로 변환 (탭으로 구분하여 깔끔하게)
        table_text = df.to_string(index=False)

        requests = [
            {'replaceAllText': {'containsText': {'text': '{{학번}}', 'matchCase': True}, 'replaceText': report_data.get('student_id', '')}},
            {'replaceAllText': {'containsText': {'text': '{{이름}}', 'matchCase': True}, 'replaceText': report_data.get('name', '')}},
            {'replaceAllText': {'containsText': {'text': '{{실험제목}}', 'matchCase': True}, 'replaceText': report_data.get('title', '')}},
            {'replaceAllText': {'containsText': {'text': '{{결과분석}}', 'matchCase': True}, 'replaceText': report_data.get('analysis', '')}},
            {'replaceAllText': {'containsText': {'text': '{{결론}}', 'matchCase': True}, 'replaceText': report_data.get('conclusion', '')}},
            # 2. 표 데이터를 텍스트로 교체
            {'replaceAllText': {'containsText': {'text': '{{측정결과_표}}', 'matchCase': True}, 'replaceText': table_text}},
        ]

        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        return True
    except Exception as e:
        st.error(f"Google Docs 업데이트 중 오류 발생: {e}")
        return False

# --- 메인 애플리케이션 ---

st.title("🧪 과학 실험 보고서 작성 도우미 (템플릿 버전)")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 1. 사용자 로그인
if not st.session_state.logged_in:
    st.subheader("👤 로그인")
    student_id = st.text_input("학번을 입력하세요.", key="login_student_id")
    password = st.text_input("비밀번호를 입력하세요.", type="password", key="login_password")
    
    if st.button("로그인/등록"):
        if student_id and password:
            worksheet = connect_to_gsheet()
            if worksheet:
                with st.spinner("로그인 중..."):
                    data = load_student_data(worksheet, student_id)
                    
                    if data.get('password_hash') is None:
                        data['password_hash'] = hash_password(password)
                        st.session_state.student_id = student_id
                        st.session_state.student_data = data
                        save_student_data(worksheet, student_id, data)
                        st.session_state.logged_in = True
                        st.success("등록 완료! 보고서 작성을 시작하세요.")
                        st.rerun()
                    elif verify_password(data['password_hash'], password):
                        st.session_state.student_id = student_id
                        st.session_state.student_data = data
                        st.session_state.logged_in = True
                        st.success("로그인 되었습니다.")
                        st.rerun()
                    else:
                        st.error("비밀번호가 일치하지 않습니다.")
        else:
            st.warning("학번과 비밀번호를 모두 입력해주세요.")

# 2. 로그인 후 메인 화면
if st.session_state.logged_in:
    student_id = st.session_state.student_id
    data = st.session_state.student_data
    worksheet = connect_to_gsheet()
    
    st.sidebar.success(f"{student_id}님, 환영합니다!")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.student_id = None
        st.session_state.student_data = None
        st.rerun()

    with st.sidebar:
        st.header("🔬 실험 정보")
        st.subheader("🎯 실험 목표")
        st.markdown("- 중화 반응의 원리를 이해한다.\n- 지시약을 이용해 중화점을 찾을 수 있다.")
        st.subheader("🔭 이론적 배경")
        st.markdown("산과 염기가 반응하여 물과 염을 생성하는 중화 반응은 화학의 기본 개념입니다.")
        st.subheader("🛠️ 실험 도구")
        st.markdown("- 0.1M HCl 표준용액\n- 미지 농도의 NaOH 용액\n- 페놀프탈레인 지시약 등")

    st.header("📄 보고서 작성")

    st.subheader("📝 Google Docs 실험 보고서")
    if data.get('doc_id'):
        doc_url = f"https://docs.google.com/document/d/{data['doc_id']}/edit"
        st.info("작성 내용은 아래 Google Docs 문서와 연동됩니다.")
        st.markdown(f"**[🔗 실험 보고서 문서 바로가기]({doc_url})**")
    else:
        st.info("아직 개인 보고서가 없습니다. 아래 버튼을 눌러 생성하세요.")
        if st.button("🚀 내 보고서 생성하기 (템플릿 기반)"):
            drive_service = get_google_api_service('drive', 'v3')
            if drive_service:
                with st.spinner("템플릿으로 문서를 생성하는 중..."):
                    template_id = st.secrets["connections"]["gsheets"]["template_doc_id"]
                    doc_title = f"{student_id} {data.get('name', '')} - 실험 보고서"
                    doc_id = create_doc_from_template(drive_service, template_id, doc_title)
                    if doc_id:
                        data['doc_id'] = doc_id
                        save_student_data(worksheet, student_id, data)
                        st.session_state.student_data['doc_id'] = doc_id
                        st.success("보고서가 성공적으로 생성되었습니다!")
                        st.rerun()

    st.divider()

    data["title"] = st.text_input("실험 제목", value=data.get("title"))
    data["name"] = st.text_input("이름", value=data.get("name"))

    st.subheader("📊 측정 결과")
    # 저장된 데이터가 dict 리스트 형태이므로 DataFrame으로 변환
    measurements_df = pd.DataFrame(data['measurements'])
    edited_df = st.data_editor(measurements_df, num_rows_to_add=1, key="measurements_editor")
    data['measurements'] = edited_df.to_dict('records')

    st.subheader("📈 실험 결과 및 분석")
    data["analysis"] = st.text_area("분석 내용", value=data.get("analysis"), height=200)

    st.subheader("💡 결론 및 고찰")
    data["conclusion"] = st.text_area("결론 내용", value=data.get("conclusion"), height=200)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 임시 저장하기", use_container_width=True):
            save_student_data(worksheet, student_id, data)
            st.session_state.student_data = data

    with col2:
        if st.button("🔄 Google Docs에 업데이트", type="primary", use_container_width=True):
            if data.get('doc_id'):
                docs_service = get_google_api_service('docs', 'v1')
                if docs_service:
                    with st.spinner("Google Docs를 업데이트하는 중..."):
                        update_data = data.copy()
                        update_data['student_id'] = student_id
                        if update_doc_with_data(docs_service, data['doc_id'], update_data):
                            st.success("Google Docs 업데이트 완료!")
            else:
                st.warning("먼저 '내 보고서 생성하기'를 눌러주세요.")

