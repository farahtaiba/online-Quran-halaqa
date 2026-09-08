# THE ONLINE QUR’AN HALAQA — Final Flask Project

Teacher: **Bilal Ahmad Ganie**

## Included
- Premium maroon/burgundy + gold responsive design
- Official supplied logo in header and hero
- Home, About, Courses, Schedule, Contact
- Authentic Qur’an Ayah of the Day seed: Taha 20:114
- Student registration/login with password hashing
- Student profile and dashboard
- Worksheet download + PDF/JPG/JPEG/PNG submission
- Submission states: Submitted, Under Review, Checked
- Teacher feedback and corrected-file upload
- Teacher dashboard with student management
- Course add/hide/show management
- Announcements
- Ayah of the Day management
- SQLite database
- Mobile hamburger navigation and responsive cards/forms

## Windows setup (recommended when PowerShell activation is blocked)

Open this project folder in VS Code, then in the terminal run:

```powershell
py -m pip install -r requirements.txt
py app.py
```

Open: `http://127.0.0.1:5000`

Do not close the terminal while the website is running.

## Teacher demo login
Email: `teacher@halaqa.local`
Password: `ChangeMe123!`

Change the demo password and set a secure SECRET_KEY before any real deployment.

## Student workflow
Teacher uploads worksheet → Student downloads → Student completes → Student uploads → Teacher reviews → Teacher adds feedback/corrected file → Student downloads corrected file.

## Important religious-content note
The seeded Ayah is Qur’an 20:114: `رَّبِّ زِدْنِي عِلْمًا` with English “My Lord, increase me in knowledge.” and Urdu “اے میرے رب! میرے علم میں اضافہ فرما۔”. Review religious text/translations with a trusted qualified source before public launch. Do not add unverified Qur’an or Hadith content.
