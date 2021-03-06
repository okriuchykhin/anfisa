import os
from app.filter.condition import ConditionMaker
from app.filter.sol_pack import SolutionPack
#===============================================
sCfgFilePath = os.path.dirname(os.path.abspath(__file__)) + "/files/"

def cfgPath(fname):
    global sCfgFilePath
    return sCfgFilePath + fname

def cfgPathSeq(fnames):
    return [cfgPath(fname) for fname in fnames]

#===============================================
sSolutionsAreSet = False

def condition_consequence_xBrowse ():
    return ConditionMaker.condEnum("Transctipt_consequence", [
            "splice_acceptor_variant",
            "splice_donor_variant",
            "stop_gained",
            "frameshift_variant",
            "inframe_insertion",
            "inframe_deletion",
            "missense_variant",
            "protein_altering_variant",
            "incomplete_terminal_codon_variant",
            "synonymous_variant",
            "splice_region_variant",
            "coding_sequence_variant"
        ])


def condition_high_quality():
    return [
        ConditionMaker.condEnum("FT", ["PASS"]),
        ConditionMaker.condNum("Proband_GQ", [60, None]),
        ConditionMaker.condNum("Min_GQ", [40, None]),
        ConditionMaker.condNum("QD", [4, None]),
        ConditionMaker.condNum("FS", [None, 30]),
    ]


def prepareSolutions():
    global sSolutionsAreSet
    if sSolutionsAreSet:
        return
    sSolutionsAreSet = True
    base_pack = SolutionPack("BASE")
    SolutionPack.regDefaultPack(base_pack)
    SolutionPack.regPack(base_pack)

    # BGM Filters, should belong to "Undiagnosed Patients Solution Pack"
    base_pack.regFilterWS("BGM_De_Novo", [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Callers", ["BGM_BAYES_DE_NOVO", "RUFUS"])]
        ,requires = {"trio_base"})

    base_pack.regFilterWS("BGM_Homozygous_Rec", [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Callers", ["BGM_HOM_REC"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"]),
        ConditionMaker.condInheritance("Inheritance_Mode",
            ["Homozygous Recessive"])],
        requires = {"trio_base"})

    base_pack.regFilterWS("BGM_Compound_Het", [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Callers", ["BGM_CMPD_HET"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"]),
        ConditionMaker.importVar("Compound_Het_transcript"),
        ConditionMaker.condEnum("Compound_Het_transcript", ["Proband"])],
        requires = {"trio_base"})

    base_pack.regFilterWS("BGM_Autosomal_Dominant", [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Callers", ["BGM_DE_NOVO"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"])],
        requires = {"trio_base"})

    # Standard mendelian Filters, should belong to "Undiagnosed Patients Solution Pack"
    base_pack.regFilterWS("Mendelian_Homozygous_Rec", condition_high_quality() + [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"]),
        ConditionMaker.condInheritance("Inheritance_Mode",
            ["Homozygous Recessive"])],
        requires = {"trio_base"})

    base_pack.regFilterWS("Mendelian_Compound_Het", condition_high_quality() + [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"]),
        ConditionMaker.importVar("Compound_Het_transcript"),
        ConditionMaker.condEnum("Compound_Het_transcript", ["Proband"])],
        requires = {"trio_base"})

    base_pack.regFilterWS("Mendelian_Auto_Dom", condition_high_quality() + [
        condition_consequence_xBrowse(),
        ConditionMaker.condEnum("Transcript_biotype", ["protein_coding"]),
        ConditionMaker.condEnum("Transcript_source", ["Ensembl"]),
        ConditionMaker.condInheritance("Inheritance_Mode",
            ["Autosomal Dominant"])],
        requires = {"trio_base"})


    # SEQaBOO Filters, should belong to "Hearing Loss Solution Pack"
    base_pack.regFilterWS("SEQaBOO_Hearing_Loss_v_01", [
        ConditionMaker.condEnum("Rules", ["SEQaBOO_Hearing_Loss_v_01"]),
        ConditionMaker.condEnum("Rules", ["ACMG59"], "NOT")])
    base_pack.regFilterWS("SEQaBOO_Hearing_Loss_v_02", [
        ConditionMaker.condEnum("Rules", ["SEQaBOO_Hearing_Loss_v_02"]),
        ConditionMaker.condEnum("Rules", ["ACMG59"], "NOT")])
    base_pack.regFilterWS("SEQaBOO_Hearing_Loss_v_03", [
        ConditionMaker.condEnum("Rules", ["SEQaBOO_Hearing_Loss_v_03"]),
        ConditionMaker.condEnum("Rules", ["ACMG59"], "NOT")])
    base_pack.regFilterWS("SEQaBOO_Hearing_Loss_v_03_5", [
        ConditionMaker.condEnum("Rules", ["SEQaBOO_Hearing_Loss_v_03"]),
        ConditionMaker.condEnum("Panels", ["All_Hearing_Loss"])])

    # SEQaBOO Filters, should belong to "Base Solution Pack"
    base_pack.regFilterWS("SEQaBOO_ACMG59", [
        ConditionMaker.condEnum("Rules", ["SEQaBOO_ACMG59"]),
        ConditionMaker.condEnum("Rules", ["ACMG59"], "AND")])

    #base_pack.regFilterXL(?, ?)

    # Production Decision Trees
    base_pack.regTreeCode("BGM xBrowse Alt",
        cfgPathSeq(["bgm_xbrowse.pyt"]),
        requires = {"trio_base"})
    base_pack.regTreeCode("Trio Candidates",
        cfgPathSeq(["quality.pyt", "rare.pyt", "trio.pyt"]),
        requires = {"trio_base"})
    base_pack.regTreeCode("All Rare Variants",
        cfgPathSeq(["quality.pyt", "rare.pyt", "return_true.pyt"]))
    base_pack.regTreeCode("Hearing Loss, v.4",
        cfgPathSeq(["quality.pyt", "hearing_loss.pyt"]))
    base_pack.regTreeCode("Hearing Loss, v.2",
        cfgPathSeq(["quality.pyt", "hearing_loss_v2.pyt"]))
    base_pack.regTreeCode("ACMG59",
        cfgPathSeq(["quality.pyt", "acmg59.pyt"]))

    # Test trees
    # base_pack.regTreeCode("Q Test",
    #     cfgPathSeq(["quality.pyt", "return_true.pyt"]))
    # base_pack.regTreeCode("R Test",
    #     cfgPathSeq(["rare.pyt", "return_true.pyt"]))
    # base_pack.regTreeCode("T Test",
    #     [cfgPath("trio.pyt")],
    #     requires = {"trio_base"})
    # base_pack.regTreeCode("H Test",
    #     [cfgPath("hearing_loss.pyt")])

    base_pack.regPanel("Symbol", "ACMG59",
        cfgPath("acmg59.lst"))
    base_pack.regPanel("Symbol", "All_Hearing_Loss",
        cfgPath("all_hearing_loss.lst"))
    base_pack.regPanel("Symbol", "Reportable_Hearing_Loss",
        cfgPath("rep_hearing_loss.lst"))
    base_pack.regPanel("Symbol", "PF",
        cfgPath("rep_purpura_fulminans.lst"))
    base_pack.regPanel("Symbol", "PharmKB_VIP",
        cfgPath("pharmgkb_vip.lst"))

