import sqlite3

DB = "clinical_knowledge.db"

RULES = [
    ("Pregnancy", "5640", "Ibuprofen", "CRITICAL", "Risk of fetal renal dysfunction and premature closure of ductus arteriosus when NSAIDs are taken during late pregnancy."),
    ("Pregnancy", "2193", "Naproxen", "CRITICAL", "NSAIDs in pregnancy cause oligohydramnios via fetal renal effects and premature ductal closure."),
    ("Pregnancy", "31708", "Lisinopril", "CRITICAL", "ACE inhibitors cause fetal renin-angiotensin system disruption, oligohydramnios, and neonatal renal failure."),
    ("Asthma", "8745", "Propranolol", "CRITICAL", "Non-selective beta-blocker can cause severe bronchoconstriction and trigger life-threatening asthma attacks."),
    ("Heart Failure", "5640", "Ibuprofen", "HIGH", "NSAIDs cause sodium and fluid retention, which can acutely worsen congestive heart failure symptoms."),
    ("Chronic Kidney Disease", "114488", "Spironolactone", "HIGH", "Potassium-sparing diuretic increases the risk of severe hyperkalemia in patients with pre-existing renal impairment."),
    ("Diabetes", "8896", "Pseudoephedrine", "MEDIUM", "Sympathomimetic decongestant can cause vasoconstriction and raise blood glucose levels, complicating diabetes management."),
]

conn = sqlite3.connect(DB)
conn.execute("DROP TABLE IF EXISTS clinical_rules")
conn.execute("""
    CREATE TABLE clinical_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_keyword TEXT NOT NULL,
        rxnorm_code TEXT NOT NULL,
        medication_name TEXT NOT NULL,
        severity TEXT NOT NULL,
        justification TEXT NOT NULL
    )
""")
conn.executemany(
    "INSERT INTO clinical_rules (condition_keyword, rxnorm_code, medication_name, severity, justification) VALUES (?, ?, ?, ?, ?)",
    RULES
)
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM clinical_rules").fetchone()[0]
print(f"Seeded {count} clinical rules into {DB}")
conn.close()
