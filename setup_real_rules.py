import sqlite3

DB = "clinical_knowledge.db"

RULES = [
    ("Pregnancy", "5640", "Ibuprofen", "CRITICAL", "Risk of fetal renal dysfunction and premature closure of ductus arteriosus when NSAIDs are taken during late pregnancy."),
    ("Pregnancy", "2193", "Naproxen", "CRITICAL", "NSAIDs in pregnancy cause oligohydramnios via fetal renal effects and premature ductal closure."),
    ("Pregnancy", "31708", "Lisinopril", "CRITICAL", "ACE inhibitors cause fetal renin-angiotensin system disruption, oligohydramnios, and neonatal renal failure."),
    ("Pregnancy", "6865", "Methotrexate", "CRITICAL", "Methotrexate is a known teratogen causing CNS, cardiac, and skeletal fetal malformations."),
    ("Pregnancy", "6922", "Valproic Acid", "CRITICAL", "Valproate causes neural tube defects and cognitive impairment in children exposed in utero."),
    ("Asthma", "8745", "Propranolol", "CRITICAL", "Non-selective beta-blocker can cause severe bronchoconstriction and trigger life-threatening asthma attacks."),
    ("Asthma", "312", "Carvedilol", "CRITICAL", "Non-selective beta-blockade precipitates acute bronchospasm in asthmatic patients."),
    ("Asthma", "1191", "Aspirin", "HIGH", "Aspirin-exacerbated respiratory disease (AERD) causes severe bronchospasm in aspirin-sensitive asthmatics."),
    ("Asthma", "5640", "Ibuprofen", "HIGH", "NSAIDs can trigger bronchospasm via leukotriene pathway in aspirin-sensitive asthma patients."),
    ("Heart Failure", "5640", "Ibuprofen", "HIGH", "NSAIDs cause sodium and fluid retention, which can acutely worsen congestive heart failure symptoms."),
    ("Heart Failure", "3672", "Celecoxib", "HIGH", "COX-2 inhibitors promote sodium retention and reduce diuretic efficacy, exacerbating heart failure."),
    ("Heart Failure", "8600", "Pioglitazone", "MEDIUM", "Thiazolidinediones cause plasma volume expansion and can precipitate or worsen heart failure."),
    ("Chronic Kidney Disease", "114488", "Spironolactone", "HIGH", "Potassium-sparing diuretic increases the risk of severe hyperkalemia in patients with pre-existing renal impairment."),
    ("Chronic Kidney Disease", "5640", "Ibuprofen", "HIGH", "NSAIDs reduce renal blood flow via prostaglandin inhibition, accelerating GFR decline."),
    ("Chronic Kidney Disease", "6809", "Metformin", "MEDIUM", "Metformin accumulates in renal impairment, increasing lactic acidosis risk; contraindicated if eGFR < 30."),
    ("Diabetes", "8896", "Pseudoephedrine", "MEDIUM", "Sympathomimetic decongestant can cause vasoconstriction and raise blood glucose levels, complicating diabetes management."),
    ("Diabetes", "5870", "Prednisone", "HIGH", "Corticosteroids induce insulin resistance and impair glucose tolerance via gluconeogenesis stimulation."),
    ("Diabetes", "2360", "Propranolol", "HIGH", "Propranolol blocks glycogenolysis and masks tachycardia from hypoglycemia, delaying treatment."),
    ("COPD", "312", "Carvedilol", "HIGH", "Non-selective beta-blockers antagonize beta-2 receptors in bronchial smooth muscle, worsening COPD."),
    ("COPD", "2360", "Propranolol", "HIGH", "Propranolol blocks beta-2-mediated bronchodilation and can decompensate COPD patients."),
    ("QT Prolongation", "1447", "Amiodarone", "CRITICAL", "Amiodarone blocks cardiac potassium channels, prolonging QT interval and risking torsades de pointes."),
    ("QT Prolongation", "6456", "Sotalol", "CRITICAL", "Sotalol prolongs repolarization via IKr blockade; dose-dependent risk of torsades de pointes."),
    ("Bradycardia", "687", "Metoprolol", "HIGH", "Beta-blockers can exacerbate bradycardia by blocking sympathetic drive to the sinoatrial node."),
    ("Bradycardia", "656659", "Verapamil", "HIGH", "Non-dihydropyridine CCBs slow AV conduction and can cause profound bradycardia."),
    ("Peptic Ulcer Disease", "1191", "Aspirin", "CRITICAL", "Aspirin inhibits COX-1, reducing gastric mucosal prostaglandin protection and promoting ulcer formation."),
    ("Peptic Ulcer Disease", "8048", "Ketorolac", "CRITICAL", "Ketorolac is the most potent GI-bleeding NSAID; contraindicated in active peptic ulcer disease."),
    ("Seizure Disorder", "6865", "Methotrexate", "HIGH", "High-dose methotrexate can cause neurotoxicity and lower seizure threshold."),
    ("Seizure Disorder", "4025", "Bupropion", "HIGH", "Bupropion lowers seizure threshold in a dose-dependent manner; contraindicated in epilepsy."),
    ("Liver Disease", "378", "Diclofenac", "HIGH", "Diclofenac is associated with elevated transaminases and rare severe hepatotoxicity."),
    ("Liver Disease", "2193", "Naproxen", "HIGH", "Naproxen hepatotoxicity risk increases in patients with pre-existing liver impairment."),
    ("Hyperkalemia", "114488", "Spironolactone", "CRITICAL", "Spironolactone competitively inhibits aldosterone, reducing potassium excretion and causing hyperkalemia."),
    ("Hyperkalemia", "3101", "Eplerenone", "CRITICAL", "Eplerenone blocks aldosterone receptors, leading to potassium retention and hyperkalemia risk."),
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
