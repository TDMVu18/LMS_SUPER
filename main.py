from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import torch
import sys
import pandas as pd
import difflib
import random
import string
import numpy as np
from transformers import T5ForConditionalGeneration, T5Tokenizer
import json
import re
from sqlalchemy.dialects.mysql import LONGTEXT
import textract
from mlxtend.frequent_patterns import apriori, association_rules
import en_core_web_sm
spc_en = en_core_web_sm.load()



app = Flask(__name__)
app.secret_key = "Secret Key"

app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://root:''@localhost/lms'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    summarize = db.Column(LONGTEXT)
    issumm = db.Column(db.Integer)
    filepath = db.Column(db.String(100))
    question = db.Column(LONGTEXT)

    def __init__(self, summarize, issumm, filepath, question):
        self.summarize = summarize
        self.issumm = issumm
        self.filepath = filepath
        self.question = question
        
class Submit(db.Model):
    id = db.Column(db.String(21), primary_key = True)
    answer = db.Column(db.String(255))
    corrected_answer = db.Column(db.String(255))
    rank = db.Column(db.String(100))
    id_ass = db.Column(db.String(21))
    id_user = db.Column(db.String(21))

    def __init__(self, id, answer, corrected_answer, rank, id_ass, id_user):
        self.id = id
        self.answer = answer
        self.corrected_answer = corrected_answer
        self.rank = rank
        self.id_ass = id_ass
        self.id_user = id_user

# Recommend khóa học
# course = pd.read_csv("archive/course.csv")
# course = course.drop(['Unnamed: 0', 'Course_id'], axis=1)
# course_ids = [str(i).zfill(4) for i in range(1, len(course) + 1)]

# # Thêm cột "Course_id" vào DataFrame
# course.insert(0, 'Course_id', course_ids)
def generate_id(length):
    characters = string.ascii_letters + string.digits

    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string

# history = pd.read_csv("history.csv", encoding='latin-1')
# data = list(history['History_course_id'].apply(lambda x:x.split(",") ))

# from mlxtend.preprocessing import TransactionEncoder
# a = TransactionEncoder()
# a_data = a.fit(data).transform(data)
# df = pd.DataFrame(a_data,columns=a.columns_)
# df = df.replace(False,0)

# df2 = df
# apriori_t = apriori(df2, min_support = 0.01, use_colnames = True, verbose = 1)
# df_ar = association_rules(apriori_t, metric = "confidence", min_threshold = 0.6)

# for n, antecedents in enumerate(df_ar['antecedents']):
#     if isinstance(antecedents, frozenset):
#         antecedents = list(antecedents)
#     antecedent_ids = ','.join(map(str, antecedents)).strip()  # Chuyển thành danh sách và tách các ID

#     antecedent_names = []
#     for antecedent_id in antecedent_ids.split(','):
#         antecedent_id = antecedent_id.strip()
#         result = course.loc[course['Course_id'] == antecedent_id]['Course Name'].iloc[0]
#         antecedent_names.append(result)

#     antecedent_names_str = ', '.join(antecedent_names)

#     consequents = df_ar['consequents'][n]
#     if isinstance(consequents, frozenset):
#         consequents = list(consequents)
#     consequent_ids = ','.join(map(str, consequents)).strip()  # Chuyển thành danh sách và tách các ID

#     consequent_names = []
#     for consequent_id in consequent_ids.split(','):
#         consequent_id = consequent_id.strip()
#         result = course.loc[course['Course_id'] == consequent_id]['Course Name'].iloc[0]
#         consequent_names.append(result)

#     consequent_names_str = ', '.join(consequent_names)

# def recommend_courses(enrolled_courses, df_ar, num_recommendations=5):
#     # Tạo một danh sách để lưu trữ các khoá học được đề xuất
#     recommended_courses = []

#     # Duyệt qua từng tập luật kết hợp trong df_ar
#     for index, row in df_ar.iterrows():
#         antecedents = row['antecedents']
#         consequents = row['consequents']

#         # Chuyển các ID trong antecedents thành các ID không có khoảng cách
#         antecedents_cleaned = [course_id.replace(" ", "") for course_id in antecedents]

#         # Kiểm tra nếu có ít nhất một khoá học từ antecedents có trong danh sách enrolled_courses
#         if any(course_id in antecedents_cleaned for course_id in enrolled_courses):
#             # Lấy danh sách các khoá học trong consequents
#             recommended_courses.extend(consequents)

#     # Loại bỏ các khoá học đã đăng ký và lặp lại
#     recommended_courses = list(set(recommended_courses) - set(enrolled_courses))

#     # Chọn một số lượng giới hạn của khoá học để đề xuất
#     if len(recommended_courses) > num_recommendations:
#         recommended_courses = recommended_courses[:num_recommendations]

#     return recommended_courses

# def zip4id(id):
#     stringid = str(id)    
#     if len(stringid) < 4:
#         stringid = '0' * (4 - len(stringid)) + stringid
#     return stringid

# model_name = 'gec_03' # model path
# torch_device = 'cuda' if torch.cuda.is_available() else 'cpu'
# tokenizer = T5Tokenizer.from_pretrained(model_name)
# model = T5ForConditionalGeneration.from_pretrained(model_name).to(torch_device)

# def correct_grammar(input_text,num_return_sequences):
#   batch = tokenizer([input_text],truncation=True,padding='max_length',max_length=64, return_tensors="pt").to(torch_device)
#   translated = model.generate(**batch,max_length=64,num_beams=4, num_return_sequences=num_return_sequences, temperature=1.5)
#   tgt_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
#   return tgt_text

# def highlight(correct_sentence, error_Sentence):
#     differ = difflib.Differ()
#     diff = list(differ.compare(correct_sentence.split(), error_Sentence.split()))

#     highlighted_diff = []
#     for word in diff:
#         if word.startswith(' '):
#             highlighted_diff.append(word[2:])
#         elif word.startswith('- '):
#             highlighted_diff.append('<span style="background-color: 7ED957;">{}</span>'.format(word[2:]))
    
#     highlighted_sentence = ' '.join(highlighted_diff)

#     return highlighted_sentence

#question-gen:

model_name = "t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def summarize_file(filepath):
    text = textract.process(filepath, encoding='utf-8')
    # Sử dụng biểu thức chính quy để cắt thành các đoạn văn
    all_paragraphs = re.split(r'\s{2,}', text.decode('utf-8'))
    num_paragraph= len(text)
    list_para = []
    list_para = [para for para in all_paragraphs if len(para.split()) >= 20] # list of paragraphs which have more than 20 words
    summaries = []
    for i,paragraph in enumerate(list_para):
        input_text = "summarize: " + paragraph
        input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = model.generate(input_ids, max_length=150, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append(summary)

    result = [{"paragraph": list_para[i], "summary": summaries[i]} for i in range(len(summaries))]
    return result


sys.path.insert(1, 'question_generator')
from questiongenerator import QuestionGenerator
qg = QuestionGenerator()

def new_question(result):
    pick_summ = len(result)
    summ_cal = random.sample(range(pick_summ), 3)
    question = []
    for i in range(len(summ_cal)):
        text = result[summ_cal[i]]["summary"]
        q  = qg.generate(text, num_questions=1)
        question.append(q)
    return question





@app.route('/get-file-path', methods=['POST'])
def process_uploaded_file():
    # Nhận đường dẫn của file
    uploaded_file_path = request.form['uploaded_file_path']
    summ = summarize_file(uploaded_file_path)
    question = new_question(summ)
    # thêm record vào csdl
    my_data = Assignment("content summarized", 1, str(uploaded_file_path), str(question))
    db.session.add(my_data)
    db.session.commit()
    return question

# @app.route('/recommend-id', methods=['POST'])
# def apriori():
#     data = request.get_json()

#     if data is not None:
#         print("json:",data)
#         enrolled = []
#         course_target = []
#         for item in data:
#             item = str(item)
#             itemstr = zip4id(item)
#             enrolled.append(itemstr)
#         print("list:", enrolled)
#         recommend = recommend_courses(enrolled, df_ar)
#         course_dict = dict(zip(course['Course_id'], course['Course Name']))
#         for course_id in enrolled:
#             clean_course_id = course_id.replace(" ", "")
#             course_name = course_dict.get(clean_course_id, 'Not Found') 
#         for course_id in recommend:
#             clean_course_id = course_id.replace(" ", "")
#             course_name = course_dict.get(clean_course_id, 'Not Found') 
#             if clean_course_id not in enrolled:
#                 target = int(clean_course_id)
#                 course_target.append(target)
#         print(course_target)
#         return course_target
#     else:
#         return jsonify({'Error': 'Request Failed UwU'})
    
# @app.route('/grammar-correct', methods=['POST'])
# def grammar_corr():
#     my_data = Submit.query.get(id)
#     sentence = my_data.answer
#     correct_list = correct_grammar(sentence, 2)
#     for i in range(2):
#         correct_list[i] = highlight(correct_list[i], sentence)    
    
#     my_data.corrected_answer = str(correct_list) 
#     db.session.commit()
#     return correct_list
if __name__ == "__main__":
    app.run(debug= True)
