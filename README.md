# 🧪 AI 과학 실험 보고서 앱 종합 실행 가이드

이 문서는 Streamlit, Google Cloud, Gemini AI를 연동하여 'AI 피드백 기능이 탑재된 과학 실험 보고서 앱'을 처음부터 끝까지 설정하고 실행하는 방법을 안내하는 종합 가이드입니다.

## 📝 전체 과정 요약앱을 실행하기까지의 전체 과정은 크게 4단계로 나뉩니다.
1. PC 환경 설정: 내 컴퓨터에 필요한 프로그램을 설치하고 프로젝트 폴더를 구성합니다.
2. Google Cloud 설정: 앱이 데이터를 저장하고 문서를 생성할 수 있도록 Google의 클라우드 서비스를 설정하고 '로봇 조수(서비스 계정)'를 고용합니다.
3. Google Workspace 설정: 보고서의 원본이 될 '마스터 템플릿'과 학생 데이터를 저장할 '스프레드시트'를 준비합니다.
4.앱 실행: 모든 설정값을 연결하여 Streamlit 앱을 최종적으로 실행합니다.

## 단계 1: PC 환경 설정
### 1-1. 필요한 프로그램(라이브러리) 설치 
먼저, 터미널(Windows의 경우 '명령 프롬프트' 또는 'PowerShell')을 열고 아래 명령어를 한 줄씩 입력하여 실행합니다. 이 프로그램들은 앱을 구성하는 데 필요한 핵심 부품들입니다.

> pip install streamlit  
> pip install gspread  
> pip install pandas  
> pip install google-api-python-client  
> pip install google-auth-httplib2  
> pip install google-auth-oauthlib  
> pip install google-generativeai  

### 1-2. 프로젝트 폴더 만들기컴퓨터의 원하는 위치에 프로젝트를 담을 폴더를 만듭니다. 그리고 그 안에 app.py 파일을 저장하고, .streamlit이라는 하위 폴더를 생성합니다.

your-project-folder/       <-- 직접 만드세요  
├── .streamlit/            <-- 직접 만드세요  
└── app.py                 <-- 제공된 코드를 이 이름으로 저장하세요  

## 단계 2: Google Cloud 및 AI 설정 (API 키 발급)
이 단계에서는 우리 앱을 대신해서 구글 문서를 만들고, AI 피드백을 생성해 줄 두 종류의 '조수'를 위한 '비밀 키'를 발급받습니다.

### 2-1. Google Cloud '서비스 계정' 키 발급 (문서/시트 작업용)
이 키는 구글 드라이브, 시트, 문서 작업을 대신 처리해 줄 '로봇 조수'의 비밀 암호입니다.
#### Google Cloud Console 접속 및 프로젝트 생성:
Google Cloud Console에 접속하여 새 프로젝트를 만듭니다.
#### 필요한 API 3가지 활성화:
왼쪽 메뉴(☰) > 'API 및 서비스' >  **'라이브러리'** 로 이동합니다.
아래 3개의 API를 각각 검색하여 '사용 설정' 버튼을 클릭합니다.
1. Google Drive API, Google Sheets API, Google Docs API'서비스 계정(로봇 조수)' 생성:  
'API 및 서비스' > **'사용자 인증 정보'** 로 이동합니다.'' > **'서비스 계정'** 을 선택합니다.  
계정 이름(예: science-report-bot)을 입력하고 **'만들기 및 계속'** 을 누릅니다.  
역할 선택에서 '기본' > **'편집자(Editor)'** 를 찾아 선택하고 **'완료'** 를 누릅니다.
2. JSON 키(비밀 암호 파일) 다운로드:
방금 만든 서비스 계정의 이메일 주소를 클릭합니다.  
상단 탭에서 **'키(KEYS)'** 를 선택합니다.'' > **'새 키 만들기'** 를 클릭합니다.  
키 유형을 JSON으로 두고 **'만들기'** 를 누르면, JSON 파일이 컴퓨터로 다운로드됩니다.   
이 파일을 잘 보관하세요.
### 2-2. Google AI 'Gemini API' 키 발급 
(AI 피드백용)이 키는 학생의 글을 분석하고 피드백을 생성해 줄 'AI 선생님'을 부르기 위한 비밀 암호입니다.
1. Google AI Studio 사이트로 이동하여 로그인합니다.
2. 화면 왼쪽의 "Get API key" 메뉴를 클릭합니다.
3. "+ Create API key" 버튼을 눌러 새 API 키를 생성합니다.
4. 생성된 긴 문자열의 API 키를 복사합니다.

## 단계 3: Google Workspace 설정 
(문서 및 시트 준비)이제 로봇 조수가 사용할 서류 양식과 데이터 장부를 준비할 차례입니다.
### 3-1. '마스터 템플릿' Google Docs 문서 만들기
1. Google Docs에서 보고서의 원본이 될 새 문서를 만듭니다.
2. 원하는 대로 서식을 꾸미고, 아래 자리표시자들을 데이터가 들어갈 위치에 정확히 입력합니다.  
학번: {{학번}}  
이름: {{이름}}  
실험 제목: {{실험제목}}  
측정 결과{{측정결과_표}}  
결과 분석{{결과분석}}  
결론 및 고찰{{결론}}  
3. 오른쪽 위 '공유' 버튼을 누르고, 2-1 단계에서 만든 서비스 계정의 이메일 주소(...@...gserviceaccount.com)를 추가하여 '편집자' 권한으로 공유합니다.
4. 브라우저 주소창에서 이 문서의 ID를 복사합니다. (예: .../d/1aBCde.../edit 에서 1aBCde... 부분)
### 3-2. '학생 데이터 저장용' Google Sheets 만들기
1. Google Sheets에서 학생 데이터를 저장할 새 스프레드시트를 만듭니다.
2. 첫 번째 시트의 이름을 학생 데이터로 변경합니다.
3. '공유' 버튼을 눌러, 이 시트 역시 서비스 계정 이메일에 '편집자' 권한으로 공유합니다.
4. 브라우저 주소창에서 이 스프레드시트의 전체 URL을 복사합니다.
## 단계 4: 앱 실행
### 4-1. secrets.toml 파일 작성
1. 1-2 단계에서 만든 .streamlit 폴더 안에 secrets.toml 이라는 이름으로 새 텍스트 파일을 만듭니다.
아래 내용을 secrets.toml 파일에 그대로 복사하여 붙여넣습니다.각 항목에 맞는 값들을 채워 넣습니다.2. 2-1 단계에서 다운로드한 JSON 파일을 텍스트 편집기로 열어 해당 내용을 복사하세요.
3. 2-2, 3-1, 3-2 단계에서 복사해 둔 키, ID, URL을 붙여넣으세요. # .streamlit/secrets.toml

#### 1. Google Sheets & Docs 연결 정보
[connections.gsheets]  
spreadsheet_url = "여기에 3-2에서 복사한 Google Sheet URL을 붙여넣으세요"  
template_doc_id = "여기에 3-1에서 복사한 템플릿 문서 ID를 붙여넣으세요"  

#### 2. Google AI (Gemini) API Key
gemini_api_key = "여기에 2-2에서 복사한 Google AI Studio API 키를 붙여넣으세요"

#### 3. GCP 서비스 계정 정보 (2-1에서 다운로드한 JSON 파일 내용)
[gcp_service_account]
type = "service_account"  
project_id = "your-gcp-project-id"  
private_key_id = "your-private-key-id"  
private_key = "-----BEGIN PRIVATE KEY-----\n ... \n-----END PRIVATE KEY-----\n"  
client_email = "your-service-account-email@...gserviceaccount.com"  
client_id = "your-client-id"  
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"  
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"  
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"  
client_x509_cert_url = "[https://www.googleapis.com/](https://www.googleapis.com/)..."  

### 4-2. Streamlit 앱 실행모든 설정이 완료되었습니다! 
터미널에서 1-2 단계에서 만든 프로젝트 폴더로 이동한 후, 아래 명령어를 실행하세요.

> streamlit run app.py

이제 웹 브라우저에서 자동으로 앱이 열리고, 모든 기능을 사용하실 수 있습니다.