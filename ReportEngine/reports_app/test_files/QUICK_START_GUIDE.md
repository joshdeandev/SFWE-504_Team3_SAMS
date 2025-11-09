# Quick Start Guide - Awarding Scholarships

## 🎯 Quick Access

**URL:** http://localhost:8000/prescreening-report/

**Or from main page:** 
1. Go to http://localhost:8000/
2. Scroll to "Pre-screening Report"
3. Click "View Interactive Report"

---

## 📋 What You'll See

### Page Layout
```
┌─────────────────────────────────────────────────────────┐
│  PRE-SCREENING REPORT - AWARD SCHOLARSHIPS              │
│  Generated: November 8, 2025 6:30 PM                    │
└─────────────────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Total   │ │  Total   │ │Scholar-  │ │ Awarded  │ │ Pending  │
│Applicants│ │ Matches  │ │  ships   │ │          │ │          │
│    10    │ │    15    │ │     5    │ │     3    │ │     2    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

┌─ Engineering Excellence Scholarship ───────── 3 Qualified ─┐
│                                                             │
│  John Doe (#12345678)           │  AWARDED  │ [Award  ]    │
│  Engineering                    │ "Excellent│ [Decline]    │
│  GPA: 3.8 | Junior              │ candidate"│ [Pending]    │
│  Qualification: 92%             │  Nov 8    │              │
│                                                             │
│  Jane Smith (#87654321)         │NO DECISION│ [Award  ]    │
│  Computer Science               │           │ [Decline]    │
│  GPA: 3.9 | Senior              │           │ [Pending]    │
│  Qualification: 95%             │           │              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏆 How to Award a Scholarship

### Step 1: Find the Applicant
- Scroll through scholarship sections
- Look at qualification scores (higher is better)
- Review applicant details (GPA, major, level)

### Step 2: Click "Award" Button
```
[Award  ] ← Click this green button
[Decline]
[Pending]
```

### Step 3: Fill in the Modal

```
┌─────────────────────────────────────┐
│  Award Scholarship               × │
├─────────────────────────────────────┤
│  Applicant: John Doe                │
│  Scholarship: Engineering Excellence│
│  Decision: ✓ AWARDED                │
│                                     │
│  Comments (Optional):               │
│  ┌─────────────────────────────┐   │
│  │ Outstanding GPA and         │   │
│  │ leadership potential        │   │
│  └─────────────────────────────┘   │
│                                     │
│  Award Amount ($):                  │
│  [  5000.00  ]                      │
│                                     │
│  ☑ Create ScholarshipAward record   │
│                                     │
│           [Cancel]  [💾 Save]       │
└─────────────────────────────────────┘
```

### Step 4: Save
- Click "Save Decision"
- Page refreshes automatically
- Status updates to show "AWARDED"

---

## ❌ How to Decline an Application

Same process, but click the **red "Decline" button** instead:
```
[Award  ]
[Decline] ← Click this red button
[Pending]
```

The modal will show:
- Decision: ✗ NOT AWARDED
- No award amount field (not needed for declines)
- Comments still available for explanation

---

## 🕐 How to Mark as Pending

Click the **yellow "Pending" button**:
```
[Award  ]
[Decline]
[Pending] ← Click this yellow button
```

Use this when:
- Waiting for additional information
- Committee hasn't decided yet
- Need more time to review

---

## 💡 Tips

### Decision Status Colors
- 🟢 **Green = Awarded** - Scholarship granted
- 🔴 **Red = Not Awarded** - Application declined
- 🟡 **Yellow = Pending** - Under review
- ⚪ **Gray = No Decision** - Not yet reviewed

### Best Practices
1. **Always add comments** - Helps with record-keeping
2. **Check qualification score** - Higher scores indicate better fit
3. **Review current status** - Don't award twice accidentally
4. **Use pending status** - When you need more time
5. **Export reports** - Keep PDF/Excel copies for records

### Common Actions
- **Change a decision?** Just click a different button and save again
- **Add more comments?** Click any button and add to existing comments
- **Create award record?** Check the box when awarding (recommended)
- **Set amount?** Enter custom amount or leave blank for default

---

## 📊 Export Options

At the top of the page, you can export the full report:

```
┌─ Export Report ─────────────────────────────┐
│  [📄 Download PDF]  [📊 Download CSV]       │
│  [📗 Download Excel]                        │
└─────────────────────────────────────────────┘
```

Exports include:
- All qualified applicants
- Award decision status
- Decision comments
- Qualification scores
- Applicant details

---

## 🔐 Authentication Required

You must be logged in to:
- View the prescreening report
- Make award decisions
- See decision status

If not logged in, you'll be redirected to the login page.

---

## 📞 Need Help?

### URLs
- Main reports: http://localhost:8000/
- Prescreening: http://localhost:8000/prescreening-report/
- Admin panel: http://localhost:8000/admin/

### Database
All decisions are stored in the `AwardDecision` model and can be viewed/edited in the Django admin panel.

---

**✅ You're ready to start awarding scholarships!**
