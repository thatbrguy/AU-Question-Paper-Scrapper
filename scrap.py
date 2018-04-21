import urllib.request
import re
import os
import requests
import argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("--sem", help="Semester", choices=['1','2','3','4','5','6','7','8'])
parser.add_argument("--dept", help="Department", choices=['ece','cse','civil','mech','it','eie','eee','bme'])
args = parser.parse_args()

def get_details(sem_choice, dept_choice):
    
    semesters = {'1': 'I', '2':'II', '3':'III', '4':'IV', '5':'V', '6':'VI', '7':'VII', '8':'VIII'}
    depts = {'civil': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=Civil&dept=BE-CE&year=2013&deptdetail=B.E.%20Civil%20Engineering',
         'cse': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=CSE&dept=BE-CSE&year=2013&deptdetail=B.E.%20Computer%20Science%20and%20Engineering',
         'ece': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=ECE&dept=BE-ECE&year=2013&deptdetail=B.E.%20Electronics%20and%20Communications%20Engineering',
         'eee': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=EEE&dept=BE-EEE&year=2013&deptdetail=B.E.%20Electrical%20and%20Electronics%20Engineering',
         'mech': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=Mechanical&dept=BE-MECH&year=2013&deptdetail=B.E.%20Mechanical%20Engineering',
         'eie': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=Instrumentation&dept=BE-EIE&year=2013&deptdetail=B.E.%20Electrical%20and%20Instrumentation%20Engineering',
         'bme': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=Biomedical&dept=BE-BME&year=2013&deptdetail=B.E.%20Biomedical%20Engineering',
         'it': 'http://www.tnscholars.com/annaUnivQPUg/UgQuestionPaperSubjectList.php?dep=InformationTechnology&dept=BTECH-IT&year=2013&deptdetail=BTECH.%20Information%20Technology'
}
    sem = semesters[sem_choice]
    home_page = urllib.request.urlopen(depts[dept_choice])
    home_soup = BeautifulSoup(home_page, "html.parser")
    
    return sem, home_soup

def get_subjects(sem, home_soup):
    
    subjects = home_soup.find_all("a", {"href": re.compile('annaUniv')})
    urls = {}
    print('------------------------------------------------------------')
    print('Subjects Available:')
    print('------------------------------------------------------------')
    for sub in subjects:
        match = re.search('(?<=semesterChar=)(.*)(?=&amp;subjectTitle)', str(sub))
        if match.group() == sem:
            urlsub = re.search('(?<=href=")(.*)(?="> <div)', str(sub))
            urlsub = 'http://www.tnscholars.com/annaUnivQPUg/' + re.sub('amp;', '', urlsub.group())
            subject_string = re.search('(?<=subjectTitle=)(.*)(?=&deptdetail)', str(urlsub)).group()
            urls[subject_string] = urlsub
            print(subject_string)
    print('------------------------------------------------------------')
    
    return urls

def get_papers(urls):
    
    pdfs_subject_dict = {}
    for subject_string, url in zip(urls.keys(), urls.values()):
        page = requests.get(url).text
        soup = BeautifulSoup(page, "html.parser")
        pdf_urls = soup.find_all("a", {"href": re.compile("javascript")})
        ID = []
        for pdf_url in pdf_urls:
            match = re.search('(?<=\(\')(.*)(?=\'\))', str(pdf_url))
            ID.append(match.group())
        pdfs_subject_dict[subject_string] = ID
        
    return pdfs_subject_dict

def dump_papers(pdfs_subject_dict, sem=None, dept=None):
    
    root_dir = 'QP'
    if sem is not None:
        root_dir += '_SEM_' + sem
    if dept is not None:
        root_dir += '_DEPT_' + dept.upper()
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)
    print('Downloading')
    print('------------------------------------------------------------')
    for subject_string, id_list in zip(pdfs_subject_dict.keys(), pdfs_subject_dict.values()):
        
        child_dir = os.path.join(root_dir, subject_string)
        if not os.path.exists(child_dir):
            os.mkdir(child_dir)
        for ID in id_list:
            pdf_url = urllib.request.urlopen('http://www.tnscholars.com/annaUnivQPUg/showPdf.php?recNo=' + str(ID))
            soup = BeautifulSoup(pdf_url, "html.parser")
            pdf = soup.find_all("iframe")
            pdf_file = 'http://www.tnscholars.com/' + re.search('(?<=src=")(.*)(?=.pdf")', str(pdf)).group() + '.pdf'
            #file_name = os.path.basename(pdf_file) May not work crossplatform
            file_name = pdf_file.split('/')[-1]
            dst_path = os.path.join(root_dir, subject_string, file_name)
            try:
                get_pdf_file = urllib.request.urlopen(pdf_file)
                with open(dst_path, 'wb') as file:
                    file.write(get_pdf_file.read())
                get_pdf_file.close()
            except:
                print(file_name, '(', subject_string, ')', 'Not Available')

if __name__ == "__main__":
    
    sem, home_page = get_details(args.sem, args.dept)
    print('------------------------------------------------------------')
    print('Fetching: Dept:', args.dept.upper(), 'Sem:', sem)
    urls = get_subjects(sem, home_page)
    pdfs = get_papers(urls)
    dump_papers(pdfs, sem, args.dept)

    print('Done')
    print('------------------------------------------------------------')
