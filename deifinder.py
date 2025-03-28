import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import io
import pandas as pd
import PyPDF2
import docx

# Try importing HTMLSession for JS rendering
try:
    from requests_html import HTMLSession
    HAS_HTMLSESSION = True
except ImportError:
    HAS_HTMLSESSION = False

# Set up API keys from streamlit secrets
openai.api_key = st.secrets["openai_api_key"]
google_api_key = st.secrets.get("google_custom_search_key", None)
google_cse_id = st.secrets.get("google_cse_id", None)

# Define the keyword list (glossary)
KEYWORDS = [
    "diversity", "equity", "inclusion", "social justice", "diversity consciousness", "ableism", "accessibility", "accommodation",
    "accomplice", "accountability", "acculturation", "active listening", "adverse impact", "advocate", "AFAB/AMAB", "affirmative action",
    "ageism", "agency", "agender", "agent", "agnostic", "ally", "allyship", "American", "androgyne", "androgynous", "androgyny",
    "anti-blackness", "anti-racist", "anti‐Semitism", "aromantic", "asexual", "assigned sex", "assimilation", "at-risk", "autism",
    "bias", "bias incident", "bicultural", "bigotry", "BIPOC", "biphobia", "biracial", "bigender", "dual gender", "bisexual",
    "blind", "Brave Space", "capitalism", "categorization", "cisgender", "cis", "cisnormativity", "cissexism", "citizen",
    "civil rights", "civil union", "class", "classism", "climate", "closeted", "in the closet", "coalition", "code-switching",
    "codification", "collusion", "colonialism", "colonization", "color-blind", "colorism", "coming out", "conscious bias",
    "explicit bias", "co-option", "co-optation", "counter-narrative", "critical analysis", "critical media literacy", "Critical Race Theory",
    "culture", "cultural appropriation", "cultural competence", "cultural encapsulation", "cultural fluency", "cultural humility",
    "cultural landscape", "culturally responsive pedagogy", "D.A.C.A", "Deferred Action for Childhood Arrivals", "deaf", "decolonize",
    "demigender", "demisexual", "democracy", "denial", "dialogue", "disability", "diaspora", "dimensions of diversity",
    "direct threat", "disadvantaged", "discrimination", "disenfranchised", "diversity", "diversity consciousness", "diversity skills",
    "domestic partner", "dominant culture", "domination", "double consciousness", "drag queen", "king", "dysmorphism", "elitism",
    "emotional intelligence", "empathy", "enculturation", "equality", "equity", "equity (social)", "ESL", "essential functions of the job",
    "ethnicity", "ethnocentrism", "Euro-Centric", "female-bodied", "femme", "First Nation People", "feminism", "first generation",
    "fluid", "fluidity", "FTM", "F2M", "F to M", "fundamental attribution error", "fundamentalism", "gatekeeping", "gay", "gender",
    "gendered", "gender affirming surgery", "gender binary", "gender diversity", "gender dysphoria", "gender expression", "gender fluid",
    "gender identity", "gender-neutral", "gender-inclusive", "gender neutral pronouns", "gender non-conforming", "gender normative",
    "gender pronouns", "gender role", "genderqueer", "genocide", "gentrification", "glass ceiling", "global competency", "global perspective",
    "globalization", "glocalization", "group identity", "harassment", "hate crime", "HBCU", "hegemony", "heteronormativity",
    "heterosexism", "heterosexual", "heterosexual privilege", "homophobia", "homosexual", "horizontal hostility", "horizontal oppression",
    "HSI", "identity sphere", "immigrant", "implicit bias", "impostor syndrome", "in‐group bias", "favoritism", "in-groups", "out-groups",
    "inclusion", "inclusive excellence", "inclusive language", "Indigenous peoples", "institutional oppression", "intersectionality",
    "intercultural competency", "intergroup conflict", "internalized oppression", "internalized racism", "intersex", "invisible minority",
    "Islamophobia", "Ism", "justice", "Latinx", "lesbian", "LGBT", "LGBTQ", "LGBTQIAA+", "lines of difference", "linguicism", "lookism",
    "major bodily functions", "major life activities", "male-bodied", "marginalize", "marginalization", "media literacy", "microaggression",
    "micro-insults", "micro-invalidation", "minority", "minority groups", "minorities", "misogyny", "mobility", "model minority",
    "MSI", "MTF", "M2F", "M to F", "MTM", "FTF", "multicultural", "multiethnic", "multiplicity", "multiracial", "naming", "national origin",
    "nativism", "neocolonialization", "neo-liberalism", "neurodiversity", "non-binary", "gender variant", "nondisabled", "nonviolence",
    "non-white", "oppression", "oppression (institutionalized)", "oppression (internalized)", "overprivileged", "pangender", "pansexual",
    "passing privilege", "patriarchy", "Pell-eligible", "people-/person-first language", "people of color", "permanent resident",
    "personal identity", "pluralism", "post-racial", "prejudice", "privilege", "privileged group member", "pronouns", "protected status",
    "PWI", "pyramiding effect", "qualified individual", "queer", "queer theory", "questioning", "race", "racial and ethnic identity",
    "racial equity", "racial profiling", "racism", "racism (cultural)", "racism (individual)", "racism (institutional)", "racism (internalized)",
    "racism (structural)", "racist policy", "rankism", "reasonable accommodation", "reclaim", "refugee", "re-fencing", "exception-making",
    "religion", "religious oppression", "resilience", "respect", "restorative justice", "safe space", "same gender loving", "saliency",
    "sapiosexual", "scapegoating", "serostatus", "settler colonialism", "sex", "sexism", "sexual orientation", "sex assignment",
    "silencing", "sizeism", "social construction", "social forces", "social identity", "social identity development", "social inequality",
    "social justice", "social movement", "social oppression", "social self‐esteem", "social self‐view", "social transition", "socialization",
    "SOFFA", "solidarity", "spotlighting", "status (social status)", "stealth", "stereotype", "stereotype threat", "stigma",
    "stigmatization", "structural inequality", "subordination", "substantially limiting", "supremacy", "Survivor", "system of oppression",
    "TCU", "third gender", "tolerance", "tokenism", "transculturation", "transformative learning", "transgender", "transition",
    "transmisogyny", "transphobia", "transsexual", "Two Spirit", "unconscious bias", "underprivileged", "underrepresented communities",
    "underutilization", "undue hardship", "undocumented", "undocumented student", "union", "unisex", "universal design", "UPstander",
    "upward mobility", "upward social mobility", "veteran status", "white fragility", "white privilege", "white supremacy", "whiteness",
    "worldview", "xenophobia", "Yes Means Yes", "ze", "zir"
]

def search_keywords(text, keywords):
    """
    Search the provided text for any keywords.
    Returns a list of keywords found.
    """
    found = []
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            found.append(kw)
    return list(set(found))

##########################
# URL Processing Section #
##########################
def process_url(url):
    result = {"url": url, "keywords_found": []}
    social_domains = ["twitter.com", "facebook.com", "instagram.com", "linkedin.com", "tiktok.com"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        if any(domain in url for domain in social_domains) and HAS_HTMLSESSION:
            try:
                session = HTMLSession()
                r = session.get(url, headers=headers, timeout=15)
                r.html.render(timeout=20)
                html = r.html.html
            except Exception as render_e:
                st.warning(f"JS rendering failed for {url}: {render_e}. Falling back to plain requests.")
                r = requests.get(url, headers=headers, timeout=10)
                html = r.text
        else:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                result["error"] = f"HTTP Status Code {r.status_code}"
                return result
            html = r.text

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        found = search_keywords(text, KEYWORDS)
        result["keywords_found"] = found

        if any(domain in url for domain in social_domains):
            date = None
            time_tag = soup.find("time")
            if time_tag and time_tag.has_attr("datetime"):
                date = time_tag["datetime"]
            result["social_media_date"] = date
    except Exception as e:
        result["error"] = str(e)
    return result

#############################
# Document Processing Logic #
#############################
def process_pdf(file):
    results = []
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        for i, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            found = search_keywords(text, KEYWORDS)
            if found:
                results.append({"page": i + 1, "keywords_found": found})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def process_docx(file):
    results = []
    try:
        doc = docx.Document(file)
        for i, para in enumerate(doc.paragraphs):
            text = para.text
            found = search_keywords(text, KEYWORDS)
            if found:
                results.append({"paragraph": i + 1, "keywords_found": found})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def process_txt(file):
    results = []
    try:
        text = file.read().decode("utf-8")
        found = search_keywords(text, KEYWORDS)
        if found:
            results.append({"section": "full text", "keywords_found": found})
    except Exception as e:
        results.append({"error": str(e)})
    return results

def process_excel(file):
    results = []
    try:
        excel_data = pd.read_excel(file, sheet_name=None)
        for sheet_name, df in excel_data.items():
            all_text = " ".join(df.astype(str).values.flatten().tolist())
            found = search_keywords(all_text, KEYWORDS)
            if found:
                results.append({"sheet": sheet_name, "keywords_found": found})
    except Exception as e:
        results.append({"error": str(e)})
    return results

#######################################
# Custom CSS for Aesthetics and Layout#
#######################################
st.markdown(
    """
    <style>
    /* Main page background color */
    .reportview-container, .main {
        background-color: #e2e1e1;
    }
    /* Header styling */
    .header {
        background-color: #740B0B;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .header img {
        display: block;
        margin: 0 auto 20px auto;
    }
    .header h1 {
        color: #e2e1e1;
        margin: 0;
    }
    /* Section container styling:
       - Entire background maroon (#740B0B)
       - Text color light-gray (#e2e1e1)
       - No extra border or divider */
    .section-container {
        background-color: #740B0B;
        color: #e2e1e1;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
    /* Ensure headings and other text are visible on maroon */
    .section-container h2, .section-container h3, .section-container p, 
    .section-container label, .section-container span, .section-container div, 
    .section-container input, .section-container textarea {
        color: #e2e1e1 !important;
    }
    /* Slight tweak for text input backgrounds if you want them maroon too:
       Comment out if you prefer the default look */
    .section-container input, .section-container textarea {
        background-color: #e2e1e1 !important;
        color: #740B0B !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#################################
# Header with Logo and Title    #
#################################
st.markdown(
    """
    <div class="header">
        <img src="https://carnegiehighered.com/wp-content/uploads/2021/04/cd-logo-red.png" alt="Logo" width="150">
        <h1>Keyword Search and AI Revision Tool</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

#####################
# App Introduction  #
#####################
st.write(
    """
This app searches for specific terms related to diversity, equity, inclusion, and more within provided URLs and documents.
It outputs the URLs (or document sections) where these terms are found.
For social media URLs, it attempts to extract the date of post.
You can also paste text into the AI chat section below to receive a revised version that excludes any of the listed terms.
    """
)

##############################################
# URL Analysis Section (maroon background)   #
##############################################
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.header("URL Analysis")
url_input = st.text_input("Enter comma-separated URLs:")
url_results = []
if url_input:
    urls = [u.strip() for u in url_input.split(",") if u.strip()]
    st.info(f"Processing {len(urls)} URL(s)...")
    for url in urls:
        result = process_url(url)
        url_results.append(result)
    st.subheader("URL Analysis Results")
    for res in url_results:
        st.write(f"**URL:** {res.get('url')}")
        if "error" in res:
            st.write(f"Error: {res['error']}")
        else:
            if res.get("keywords_found"):
                st.write("**Keywords found:** " + ", ".join(res["keywords_found"]))
            else:
                st.write("No keywords found.")
            if res.get("social_media_date"):
                st.write("**Social media post date:** " + str(res["social_media_date"]))
st.markdown('</div>', unsafe_allow_html=True)

##############################################
# Document Analysis Section (maroon bg)      #
##############################################
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.header("Document Analysis")
uploaded_files = st.file_uploader(
    "Upload documents (PDF, DOCX, Excel, TXT)",
    type=["pdf", "docx", "xlsx", "xls", "txt"],
    accept_multiple_files=True
)
doc_results = {}
if uploaded_files:
    for file in uploaded_files:
        file_type = file.name.split(".")[-1].lower()
        if file_type == "pdf":
            res = process_pdf(file)
        elif file_type == "docx":
            res = process_docx(file)
        elif file_type in ["xlsx", "xls"]:
            res = process_excel(file)
        elif file_type == "txt":
            res = process_txt(file)
        else:
            res = [{"error": "Unsupported file type"}]
        doc_results[file.name] = res

    st.subheader("Document Analysis Results")
    for filename, analyses in doc_results.items():
        st.write(f"### {filename}")
        for analysis in analyses:
            if "error" in analysis:
                st.write(f"Error: {analysis['error']}")
            else:
                if "page" in analysis:
                    st.write(f"**Page {analysis['page']}:** Keywords found: " + ", ".join(analysis["keywords_found"]))
                elif "paragraph" in analysis:
                    st.write(f"**Paragraph {analysis['paragraph']}:** Keywords found: " + ", ".join(analysis["keywords_found"]))
                elif "sheet" in analysis:
                    st.write(f"**Sheet {analysis['sheet']}:** Keywords found: " + ", ".join(analysis["keywords_found"]))
                elif "section" in analysis:
                    st.write(f"**Section ({analysis['section']}):** Keywords found: " + ", ".join(analysis["keywords_found"]))
st.markdown('</div>', unsafe_allow_html=True)

####################################################
# Revision Suggestions Section (maroon background) #
####################################################
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.header("AI Chat for Revision Suggestions")
st.write(
    """
Paste in text that contains one or more of the above terms.
    """
)
user_text = st.text_area("Enter text for revision suggestions:")
if st.button("Get Revision Suggestions"):
    if user_text.strip():
        prompt = (
            f"Below is some text that may include one or more of the following terms:\n{', '.join(KEYWORDS)}\n\n"
            "Your task is to completely revise the text by removing or replacing any instances of the above keywords. "
            "The final output must not include any form of the following keywords:\n"
            f"{', '.join(KEYWORDS)}.\n\n"
            f"Text:\n{user_text}\n\n"
            "Revised text (with none of the above keywords present):"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that revises text to exclude specified terms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            suggestion = response.choices[0].message.content
            st.subheader("Revision Suggestions")
            st.write(suggestion)
        except Exception as e:
            st.error(f"Error with OpenAI API: {e}")
    else:
        st.warning("Please enter some text to revise.")
st.markdown('</div>', unsafe_allow_html=True)
