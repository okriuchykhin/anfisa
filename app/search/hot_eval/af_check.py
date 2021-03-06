def evalRec(env, rec):
    """gnomAD Frequency Threshold"""

    if rec.gnomAD_AF < env.af:
        return True
    if rec.gnomAD_AF < env.af_in_db:
        return len(rec.Presence_in_Databases & {"ClinVar", "HGMD"}) > 0
    return False
