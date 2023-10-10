from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import torch
import json
import textract
import sys
from transformers import T5ForConditionalGeneration, T5Tokenizer
import pandas as pd
import numpy as np
import re
from mlxtend.frequent_patterns import apriori, association_rules
import en_core_web_sm
spc_en = en_core_web_sm.load()

# model_name = "t5-small"
# tokenizer = T5Tokenizer.from_pretrained(model_name)
# model = T5ForConditionalGeneration.from_pretrained(model_name)
# # model_name = 'deep-learning-analytics/GrammarCorrector'
# text = textract.process('Report.pdf', encoding='utf-8')
# all_paragraphs = re.split(r'\s{2,}', text.decode('utf-8'))
# num_paragraph= len(text)
# list_para = []
# list_para = [para for para in all_paragraphs if len(para.split()) >= 20]
# summaries = []
# for i,paragraph in enumerate(list_para):
#     input_text = "summarize: " + paragraph
#     input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=1024, truncation=True)
#     summary_ids = model.generate(input_ids, max_length=150, min_length=50, length_penalty=2.0, num_beams=4, early_stopping=True)
#     summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
#     summaries.append(summary)
# result = [{"paragraph": list_para[i], "summary": summaries[i]} for i in range(len(summaries))]

# sys.path.insert(1, 'question_generator')

# from questiongenerator import QuestionGenerator
# qg = QuestionGenerator()
# text = result[2]["summary"]
# q  = qg.generate(text, num_questions=3)
# for i in range(len(q)): print(q[i]["question"])

app = Flask(__name__)
app.secret_key = "Secret Key"

app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql://root:''@localhost/moodle'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

#apriori cal
course = pd.read_csv("archive/course.csv")
course = course.drop(['Unnamed: 0', 'Course_id'], axis=1)
course_ids = [str(i).zfill(4) for i in range(1, len(course) + 1)]

# Thêm cột "Course_id" vào DataFrame
course.insert(0, 'Course_id', course_ids)

history = pd.read_csv("history.csv", encoding='latin-1')
data = list(history['History_course_id'].apply(lambda x:x.split(",") ))

from mlxtend.preprocessing import TransactionEncoder
a = TransactionEncoder()
a_data = a.fit(data).transform(data)
df = pd.DataFrame(a_data,columns=a.columns_)
df = df.replace(False,0)

df2 = df
apriori_t = apriori(df2, min_support = 0.01, use_colnames = True, verbose = 1)
df_ar = association_rules(apriori_t, metric = "confidence", min_threshold = 0.6)

for n, antecedents in enumerate(df_ar['antecedents']):
    if isinstance(antecedents, frozenset):
        antecedents = list(antecedents)
    antecedent_ids = ','.join(map(str, antecedents)).strip()  # Chuyển thành danh sách và tách các ID

    antecedent_names = []
    for antecedent_id in antecedent_ids.split(','):
        antecedent_id = antecedent_id.strip()
        result = course.loc[course['Course_id'] == antecedent_id]['Course Name'].iloc[0]
        antecedent_names.append(result)

    antecedent_names_str = ', '.join(antecedent_names)

    consequents = df_ar['consequents'][n]
    if isinstance(consequents, frozenset):
        consequents = list(consequents)
    consequent_ids = ','.join(map(str, consequents)).strip()  # Chuyển thành danh sách và tách các ID

    consequent_names = []
    for consequent_id in consequent_ids.split(','):
        consequent_id = consequent_id.strip()
        result = course.loc[course['Course_id'] == consequent_id]['Course Name'].iloc[0]
        consequent_names.append(result)

    consequent_names_str = ', '.join(consequent_names)

def recommend_courses(enrolled_courses, df_ar, num_recommendations=5):
    # Tạo một danh sách để lưu trữ các khoá học được đề xuất
    recommended_courses = []

    # Duyệt qua từng tập luật kết hợp trong df_ar
    for index, row in df_ar.iterrows():
        antecedents = row['antecedents']
        consequents = row['consequents']

        # Chuyển các ID trong antecedents thành các ID không có khoảng cách
        antecedents_cleaned = [course_id.replace(" ", "") for course_id in antecedents]

        # Kiểm tra nếu có ít nhất một khoá học từ antecedents có trong danh sách enrolled_courses
        if any(course_id in antecedents_cleaned for course_id in enrolled_courses):
            # Lấy danh sách các khoá học trong consequents
            recommended_courses.extend(consequents)

    # Loại bỏ các khoá học đã đăng ký và lặp lại
    recommended_courses = list(set(recommended_courses) - set(enrolled_courses))

    # Chọn một số lượng giới hạn của khoá học để đề xuất
    if len(recommended_courses) > num_recommendations:
        recommended_courses = recommended_courses[:num_recommendations]

    return recommended_courses

def zip4id(id):
    stringid = str(id)    
    if len(stringid) < 4:
        stringid = '0' * (4 - len(stringid)) + stringid
    return stringid





@app.route('/recommend-id', methods=['POST'])
def apriori():
    data = request.get_json()

    if data is not None:
        print("json:",data)
        enrolled = []
        course_target = []
        for item in data:
            item = str(item)
            itemstr = zip4id(item)
            enrolled.append(itemstr)
        print("list:", enrolled)
        recommend = recommend_courses(enrolled, df_ar)
        course_dict = dict(zip(course['Course_id'], course['Course Name']))
        for course_id in enrolled:
            clean_course_id = course_id.replace(" ", "")
            course_name = course_dict.get(clean_course_id, 'Not Found') 
        for course_id in recommend:
            clean_course_id = course_id.replace(" ", "")
            course_name = course_dict.get(clean_course_id, 'Not Found') 
            if clean_course_id not in enrolled:
                target = int(clean_course_id)
                course_target.append(target)
        print(course_target)
        return course_target
    else:
        return jsonify({'error': 'error'})
    



# class Mdl_assign(db.Model):
#     id = db.Column(db.Integer, primary_key = True)
#     course = db.Column(db.String(100))
#     name = db.Column(db.String(100))
#     intro = db.Column(db.String(100))
#     introformat = db.Column(db.String(100))
#     alwaysshowdescription = db.Column(db.String(100))
#     nosubmissions = db.Column(db.String(100))
#     submissiondrafts = db.Column(db.String(100))
#     sendnotifications = db.Column(db.String(100))
#     sendlatenotifications = db.Column(db.String(100))
#     duedate = db.Column(db.String(100))
#     allowsubmissionsfromdate = db.Column(db.String(100))
#     grade = db.Column(db.String(100))
#     timemodified = db.Column(db.String(100))
#     requiresubmissionstatement = db.Column(db.String(100))
#     completionsubmit = db.Column(db.String(100))
#     cutoffdate = db.Column(db.String(100))
#     gradingduedate = db.Column(db.String(100))
#     teamsubmission = db.Column(db.String(100))
#     requireallteammemberssubmit = db.Column(db.String(100))
#     teamsubmissiongroupingid = db.Column(db.String(100))
#     blindmarking = db.Column(db.String(100))
#     hidegrader = db.Column(db.String(100))
#     revealidentities = db.Column(db.String(100))
#     attemptreopenmethod = db.Column(db.String(100))
#     maxattempts = db.Column(db.String(100))
#     markingworkflow = db.Column(db.String(100))
#     markingallocation = db.Column(db.String(100))
#     sendstudentnotifications = db.Column(db.String(100))
#     preventsubmissionnotingroup = db.Column(db.String(100))
#     activity = db.Column(db.String(100))
#     activityformat = db.Column(db.String(100))
#     timelimit = db.Column(db.String(100))
#     submissionattachments = db.Column(db.String(100))
#     def __init__(self, id, course, name, intro, introformat, alwaysshowdescription, nosubmissions, submissiondrafts, 
#     sendnotifications, sendlatenotifications, duedate, allowsubmissionsfromdate, grade, timemodified,requiresubmissionstatement, completionsubmit, cutoffdate,
#     gradingduedate, teamsubmission, requireallteammemberssubmit, teamsubmissiongroupingid, blindmarking, hidegrader, revealidentities, attemptreopenmethod, maxattempts,
#     markingworkflow, markingallocation, sendstudentnotifications, preventsubmissionnotingroup, activity, activityformat, timelimit, submissionattachments):
#         self.id = id
#         self.course = course
#         self.name = name
#         self.intro = intro
#         self.introformat = introformat
#         self.alwaysshowdescription = alwaysshowdescription
#         self.nosubmissions = nosubmissions
#         self.submissiondrafts = submissiondrafts
#         self.sendnotifications = sendnotifications
#         self.sendlatenotifications = sendlatenotifications
#         self.duedate = duedate
#         self.allowsubmissionsfromdate = allowsubmissionsfromdate
#         self.grade = grade
#         self.timemodified = timemodified
#         self.requiresubmissionstatement = requiresubmissionstatement
#         self.completionsubmit = completionsubmit
#         self.cutoffdate = cutoffdate
#         self.gradingduedate = gradingduedate
#         self.teamsubmission = teamsubmission
#         self.requireallteammemberssubmit = requireallteammemberssubmit
#         self.teamsubmissiongroupingid = teamsubmissiongroupingid
#         self.blindmarking = blindmarking
#         self.hidegrader = hidegrader
#         self.revealidentities = revealidentities
#         self.attemptreopenmethod = attemptreopenmethod
#         self.maxattempts = maxattempts
#         self.markingworkflow = markingworkflow
#         self.markingallocation = markingallocation
#         self.sendstudentnotifications = sendstudentnotifications
#         self.preventsubmissionnotingroup = preventsubmissionnotingroup
#         self.activity = activity
#         self.activityformat = activityformat
#         self.timelimit = timelimit
#         self.submissionattachments = submissionattachments
            
# @app.route('/post', methods=['POST'])
# def get_data():
    
#     if request.method == 'POST':
#         record_id = request.form["id"]
#         record_to_update = Mdl_assign.query.get(record_id)
#         if record_to_update:
#             value = generate_question()
#             record_to_update.intro = value
#         db.session.commit()
#         return "Update Success"
          

# @app.route('/input-text', methods = ['GET','POST'])
# def insert():

#     if request.method == 'POST':

#         text = request.form["text"]
#         my_data = Prob(text)
#         db.session.add(my_data)
#         db.session.commit()

#         return jsonify({"message": "Dữ liệu đã được thêm vào bảng Prob thành công."})

# @app.route('/predict', methods=['POST'])
# def predict():
#     if request.method == 'POST':
#         id_to_get = request.form.get('id')

#         prob_data = Prob.query.filter_by(id=id_to_get).first()
#         if prob_data is None:
#             return jsonify({"message": "Không tìm thấy dòng với id đã cho trong bảng Prob."}), 404

#         text = prob_data.text

#         sentiment = predict_function(text)

#         result_data = Result(text=text, sentiment=sentiment)
#         db.session.add(result_data)
#         db.session.commit()
        
#         return jsonify({"message": "Dữ liệu đã được tính toán và thêm vào bảng Result thành công."})
        
# @app.route('/delete/<id>/', methods = ['GET', 'POST'])
# def delete(id):
#     my_data = Payload.query.get(id)
#     db.session.delete(my_data)
#     db.session.commit()
#     return redirect(url_for('Index'))
if __name__ == "__main__":
    app.run(debug= True)