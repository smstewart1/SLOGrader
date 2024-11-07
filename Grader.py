#import libraries
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

#global variables

current_datetime = datetime.now()
formatted_date = current_datetime.strftime('%d%m%y_%H%M')

    #input files
key_file = ".\KeyWeighted.csv"
student_responses = ".\MockStudentResponsesRows.csv"
version_list = [".\V2.csv", ".\V3.csv", "V4.csv", "V5.csv"]
                      
    #ouptut files
student_reports = f".\StudentReports_{formatted_date}.xlsx"
student_scores = f".\StudentScores_{formatted_date}.xlsx"
exam_analysis = f".\ExamAnalysis_{formatted_date}.xlsx"
student_proficiency = f".\StudentProficiency_{formatted_date}.xlsx"
section_proficiency = f".\SectionProficiency_{formatted_date}.xlsx"
heat_map_file = f".\ResponseFrequences_{formatted_date}.png"
Q_hist_file = f".\QuestionFrequences_{formatted_date}.png"
S_hist_file = f".\SectionFrequences_{formatted_date}.png"

    #analysis tools
threshhold = 0.7
question_groups = [1, 11, 21, 31, 40]

#dictionaries
Response_dictionary = {"A": 1, "B": 2, "C" : 3, "D": 4, "E": 5, "Other": 6}

#main function
def main() -> None:
    
        #read in key
    try:
        QAW_file = pd.read_csv(key_file)
    except:
        return "Key file not found"
    QAW = QAW_file.values.tolist()
    if len(QAW[0]) == 2:
        for i in range(0, len(QAW)):
            QAW[i].append(100 / len(QAW))
    del QAW_file
    
        #read in students and responses
    try:
        SR_file = pd.read_csv(student_responses)
    except:
        return "Student responses not found"
    Student_temp = SR_file.values.tolist()
    del SR_file
    Students = []
    for i, row in enumerate(Student_temp):
        Students.append(student(row[0], row[1], row[2], row[3], row[4:]))
    
        #read in answer keys
    keys = []
    for i, j in enumerate(version_list):
        try: 
            open(j, "r")
        except:
            break
        df = pd.read_csv(j, header = 0)
        keys.append(VersionControl(i, df["New Version"].values.tolist(), df[["A", "B", "C", "D", "E"]].values.tolist()))
        del df
        
        #adjust the version of the exam, grade exam, and build up frequency responses
    output = [["Last Name", "First Name", "Student ID", "Score"]]
    with pd.ExcelWriter(student_reports) as writer:
        for i, j in enumerate(Students):
            j.version_change(keys)
            j.grade(QAW)
            name = f"{j.last_name} {j.first_name}"
            if len(name) > 15:
                name = name[0:14]
            df = pd.DataFrame(j.report[1:], columns = j.report[0])
            df.index = df.index + 1
            df.to_excel(writer, sheet_name = name)
            del df
            del name
            output.append([j.last_name, j.first_name, j.student_id, j.score])
        list_to_file(output, student_scores)
        del output

        #tally frequency responses
    Frequency_report = frequency_counter(Students)
    Freq_df = pd.DataFrame(Frequency_report[1:], columns = Frequency_report[0])
    Freq_df.reset_index(drop = True, inplace = True)
    Freq_df.index = Freq_df.index + 1 
    heat_plot(Freq_df, heat_map_file)
    del Freq_df
    del Frequency_report
    
        #tally student per question performance
    Question_report = question_success(Students)
    list_to_file(Question_report, exam_analysis)
    df = pd.DataFrame(Question_report[1:], columns = Question_report[0])
    bar_plot_answers(threshhold, df, Q_hist_file)
    del df
    del Question_report
    
        #tally section performance
    if len(question_groups) == 0:
        print("No Section Analysis Done as No Ranges are Given")
    else: 
        output = section_success(Students)
        success_by_section = output[1]
        student_prof = output[0]
        list_to_file(student_prof, student_proficiency)
        df = pd.DataFrame(success_by_section[1:], columns = success_by_section[0])
        S_plot(threshhold, df, S_hist_file)
        del df
        list_to_file(success_by_section, section_proficiency)
        del success_by_section
        del student_prof
    
        #build frequency responses 
    basetable = []
    for i, _ in enumerate(QAW):
        basetable.append([i + 1, 0])
    for i, j in enumerate(Students):
        basetable[j.N_correct - 1][1] += 1
    for i, j in enumerate(basetable):
        basetable[i].append(j[1]/len(Students) * 100)
    
        #plot the basetable
    df = pd.DataFrame(basetable, columns = ["Question", "Number of Students", "Percentage of Students"])
    df.index = df.index + 1
    hist_response_success(df, "Total")
        
        #print the sections using slides
    if len(question_groups) > 0:
        for i in range(0, len(question_groups) - 1):
            hist_response_success(df.iloc[(question_groups[i] - 1):(question_groups[i + 1])], str(i + 1))
    del df
    
    return

#custom functions-----------------------------------------------------------------------------------------------------------------------------

    #report handling and calculations---------------------------------------------------------------------------------------------------------

    #output a file
def list_to_file(input: list, file: str) -> None:
    df = pd. DataFrame(input[1:], columns = input[0])
    df.reset_index(drop = True, inplace = True)
    df.index = df.index + 1 
    df.to_excel(file)
    return

    #count section frequencies
def section_success(student_lists: list) -> list:
    output = [["First Name", "Last Name", "Student ID"]]
    counting = [["Section" , "Number Proficient", "Number of Students", "Percentage Proficient"]]
    for i in range(len(question_groups) - 1):
        output[0].append(f"Section {i + 1}")
        counting.append([i + 1, 0, 0, 0])
    for i, student in enumerate(student_lists): 
        row = [student.last_name, student.first_name, student.student_id]
        for j, responses in enumerate(student.report):
            if j == 0:
                Correct = 0
            if j in question_groups[1:-1]:
                row.append(Correct)
                Correct = 0
            if responses[1]== responses[2]:
                Correct += 1    
        row.append(Correct)
        output.append(row)
    output = appended_proficiency(output)
    counting = number_prof_students(counting, output)
    for i, row in enumerate(counting):
        if i > 0:
            counting[i][3] = row[1] * 100 / row[2]
    return [output, counting]

    #count number of proficient students
def number_prof_students(count: list, output: list) -> list:
    for _, row in enumerate(output):
        for i in range(len(question_groups) - 1):
            if row[-(i + 1)] == "Proficient":
                count[-(i + 1)][1] += 1 
            count[-(i + 1)][2] += 1
    return count

    #append information to student success
def appended_proficiency(first_pass: list) -> list:
    for i, row in enumerate(first_pass):
        if i == 0:
            for j in range(len(question_groups) - 1):
                first_pass[0].append(f"Section {j + 1} Proficiency")    
        else:
            for j in range(len(question_groups) - 1):
                first_pass[i].append("Proficient" if row[3 + j] >= (question_groups[j + 1] - question_groups[j]) * threshhold else "Not Proficient") 
    return first_pass

    #count question frequencies
def question_success(student_lists: list) -> list:
    output = [["Question", "Number of Correct Responses", "Number of Students", "Percentage Correct"]]
    for i, student in enumerate(student_lists):
        if i == 0:
            for k, answers in enumerate(student.report):
                if answers[1] == answers[2] and k > 0:
                    output.append([k, 1, 1])
                elif k > 0:
                    output.append([k, 0, 1])
        else:
            for k, answers in enumerate(student.report):
                if answers[1] == answers[2] and k > 0:
                    output[k][1] += 1
                    output[k][2] += 1
                elif k > 0:
                    output[k][2] += 1
    for i, results in enumerate(output):
        if i > 0:
            results.append(100 * results[1] / results[2])
    return output

    #count the frequency of responses
def frequency_counter(students: list) -> list:
    response_map = [["Question", "A", "B", "C", "D", "E", "Other"]]
    for i, v in enumerate(students):
        if i == 0: #we have to initialize the list on the first round
            for j, w in enumerate(v.v1_responses):
                response_map.append([j, 0, 0, 0, 0, 0, 0])
                try:
                    response_map[j + 1][Response_dictionary[w]] = 1
                except:
                    response_map[j + 1][6] = 1
        else:
            for j, w in enumerate(v.v1_responses):
                try:
                    response_map[j + 1][Response_dictionary[w]] += 1
                except:
                    response_map[j + 1][6] += 1
    norm_map = [["Question", "A", "B", "C", "D", "E", "Other"]]
    for i, v in enumerate(response_map):
        indices = [1, 2, 3, 4, 5, 6]
        if i > 0:
            norm = sum(v[1:6])
            for index in indices: v[index] = v[index] * 100/ norm
            norm_map.append([i, v[1], v[2], v[3], v[4], v[5], v[6]])
            del norm
    return norm_map

    #Plotting Functions--------------------------------------------------------------------------------------------------------------

    #create a histrogram of frequencies
def hist_plot_answers(dataframe:pd, file_name: str) -> None:
    plt.figure(figure = (20, 10)).set_figwidth(15)
    plt.bar(x = dataframe["Questions"], height = dataframe["Percentage of Students"], align = 'center', color = 'green')
    plt.title("Percentage of Students Who Got A Certain Number of Questions Right")
    plt.xlabel("Number of Correct Question")
    plt.ylabel("Percentage of Students")
    plt.ylim([0, 100])
    list = dataframe["Question"].values.tolist()
    plt.xticks(range(1, len(list) + 1), labels = list)
    plt.savefig(f"./Correct_frequency_by{file_name}.png")
    plt.clf()
    del list
    return
    
    #return a heat map of frequency resposes 
def heat_plot(dataframe: pd, name: str) -> None:
    plt.figure(figsize = (10, 10)).set_figwidth(8)
    plt.rcParams['figure.figsize'] = [8, 8]
    plt.imshow(dataframe.loc[:,["A", "B", "C", "D", "E", "Other"]], cmap = "RdYlGn", vmin = 0, vmax = 100)
    plt.yticks(range(len(dataframe)), dataframe.index)
    plt.colorbar()
    plt.xticks(range(0, 6), labels = ["A", "B", "C", "D", "E", "O"])
    plt.title("Frequency Response of Answers")
    plt.xlabel("Answer")
    plt.ylabel("Question Number", loc = "center")
    plt.savefig(name)
    plt.clf()
    return

    #create a bar graph of the answer responses
def bar_plot_answers(threshhold: int, dataframe:pd, file_name: str) -> None:
    plt.figure(figure = (20, 10)).set_figwidth(15)
    plt.bar(x = dataframe["Question"], height = dataframe["Percentage Correct"], align = 'center', color = 'green')
    plt.title("Percentage of Students Who Answered Question Correctly")
    plt.xlabel("Question")
    plt.ylabel("Percentage of Students")
    plt.ylim([0, 100])
    list = dataframe["Question"].values.tolist()
    plt.xticks(range(1, len(list) + 1), labels = list)
    plt.axhline(y = threshhold * 100, linewidth = 1, color = 'k', linestyle = '--')
    plt.savefig(file_name)
    plt.clf()
    del list
    return

    #create a bar graph of the answer responses
def S_plot(threshhold: int, dataframe: pd, file_name: str) -> None:
    plt.figure(figure = (10, 10)).set_figwidth(8)
    plt.bar(x = dataframe["Section"], height = dataframe["Percentage Proficient"], align = 'center', color = 'green')
    plt.title("Percentage of Students Who Were Proficient")
    plt.xlabel("Question Group")
    plt.ylabel("Percentage of Students")
    list = dataframe["Section"].values.tolist()
    plt.xticks(range(1, len(list) + 1), labels = list)
    plt.ylim([0, 100])
    plt.axhline(y = threshhold * 100, linewidth = 1, color = 'k', linestyle = '--')
    plt.savefig(file_name)
    plt.clf()
    del list
    return

    #plot histrogram of student proficiencies
def hist_response_success(dataframe: pd, name:str, *args) -> None:
    plt.figure(figure = (10, 10)).set_figwidth(8)
    plt.bar(x = dataframe["Question"], height = dataframe["Percentage of Students"], align = 'center', color = 'green')
    plt.title("Percentage of Students Who Were Proficient")
    plt.xlabel("Question Range")
    plt.ylabel("Percentage of Students")
    list = dataframe["Question"].values.tolist()
    # plt.xticks(ticks = list, labels = list)
    plt.ylim([0, 100])
    if len(args) > 0:
        plt.axvline(y = args[0] * (max(list) - min(list)) * 100, linewidth = 1, color = 'k', linestyle = '--')
    file_name = f"./Histogram_responses_for_{name}_{formatted_date}.png"
    plt.savefig(file_name)
    plt.clf()
    del file_name
    del list
    return    
    
#custom classes---------------------------------------------------------------------------------------------------------------
class student:
    def __init__(self, first_name: str, last_name: str, student_id: int, version: str, answers: list) -> None:
        self.first_name = first_name[0] + first_name[1:].lower()
        self.last_name = last_name[0] + last_name[1:].lower()
        self.student_id = int(student_id)
        self.responses = answers
        self.v1_responses = None
        self.number_of_questions = len(answers)
        self.version = version
        self.score = None
        self.N_correct = None
        self.Section_Scores = None
        self.graded = None
        
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        return f"Gives the responses of student with ID of {self.student_id}"
    
    def grade(self, answer_key: list) -> None:
        self.graded = self.grader(answer_key)
        self.Section_Scores = self.section_grade(question_groups)
        self.score = self.scorer()
        self.report = self.generate_student_report(answer_key)
        self.N_correct = self.N_correct_function()
            
        #transform answers between versions
    def version_change(self, keys: list) -> None:
        if self.version == 1 or len(keys) == 0:
            self.v1_responses = self.responses
            return
        try:
            keys[self.version - 2]
        except:
            print(f"Invalid Version Found: Exam not Adjusted for {self.student_id}")
            self.v1_responses = self.responses
            return
        list = []
        version = keys[self.version - 2]
        #convert letter answers
        for i, j in enumerate(version.answers):
            list.append(self.question_matrix(i, j))
        #convert number answers
        corrected_list = []
        for _, j in enumerate(version.question):
            corrected_list.append(list[j - 1])
        self.v1_responses = corrected_list
        del corrected_list
        del list
        return 

        #change the letter to version 1
    def question_matrix(self, position: int, conversion: list) -> str:
        reference = ["A", "B", "C", "D", "E"]
        for i, v in enumerate(conversion):
            if v == self.responses[position]:
                return reference[i]
        return "Other"

    #check student answers
    def grader(self, answer_key: list) -> list:
        responses = []
        for i, v in enumerate(answer_key):
            if v[1] == self.v1_responses[i]:
                responses.append(v[2])
            else:
                responses.append(0)
        return responses

        #return student grade
    def scorer(self) -> float:
        score_r = 0
        for i in range(0, len(self.graded)):
            score_r += self.graded[i]
        return score_r
    
        #number of correct questions
    def N_correct_function(self) -> float:
        N = 0
        for i in range(0, len(self.graded)):
            # print(self.graded[i])
            if self.graded[i] > 0:
                N += 1
        return N
    
        #return a student report
    def generate_student_report(self, answer_key: list) -> list:
        report = [["Question", "Answer", "Correct Answer", "Value", "Correct/Incorrect"]]
        for i, v in enumerate(self.v1_responses):
            if v == answer_key[i][1]:
                report.append([i + 1, v, answer_key[i][1], answer_key[i][2], "Correct"])
            else:
                report.append([i + 1, v, answer_key[i][1], answer_key[i][2], "Incorrect"])
        return report
    
        #find a section 
    def section_grade(self, question_groups) -> list:
        if len(question_groups) == 0:
            return []
        list = [0]
        holder = 0
        for i, j in enumerate(self.graded):
            if i in question_groups[1:-1]:
                list.append(0)
                holder += 1
            if j > 0:
                list[holder] += 1
        return list

#-------------------------------------------------------------
class VersionControl:
    def __init__(self, label: int, question_input: list, answer_input: list) -> None:
            self.name = label
            self.question = question_input
            self.answers = answer_input

    def __str__(self) -> str:
        return f"Version {self.name}"
    
    def __repr__(self) -> str:
        return f"Gives the conversion function between the parent exam and exam version {self.version}"
    
#execute main
if __name__ == "__main__":
  main()
