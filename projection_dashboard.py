import pandas as pd
import streamlit as st

import functions as func
# inputs
with st.sidebar:

    # acquisition du bien
    st.header("Acquisition du bien")
    cout_bien = st.number_input("Coût d'acquisition (euros)", value=112500, min_value=0)
    superficie = st.number_input("Superficie (m2)", value=39, min_value=0)
    charges_copropriete = st.number_input("Charges de copropriété", value=240, min_value=0)
    taxe_fonciere = st.number_input("Taxe foncière annuelle (euros)", value=544, min_value=0)

    # chasseur
    st.header("Chasseur")
    honoraires_chasseur = st.number_input("Honoraires chasseur (euros)", value=0, min_value=0)

    # notaire
    st.header("Notaire")
    frais_promesse_vente = st.number_input("Honoraires de promesse de vente", value=530.0, min_value=0.0)
    frais_notaire = st.number_input("Frais de notaire (%)", value=8.6, min_value=0.0, max_value=100.0)

    # pret banque
    st.header("Prêt bancaire")
    inclure_honoraires = st.checkbox("Inclure honoraires?")
    inclure_travaux = st.checkbox("Inclure travaux?", value=True)
    inclure_meubles = st.checkbox("Inclure meubles?")

    taux_emprunt_perc = st.number_input("Taux d'emprunt (%)", value=2.0, min_value=0.0, max_value=100.0)
    taux_emprunt = taux_emprunt_perc / 100
    taux_emprunt_mensuel = pow(1 + taux_emprunt, 1/12) - 1
    taux_apport = st.number_input("Taux d'apport (%)", value=10.0, min_value=0.0, max_value=100.0)
    annees_credit = st.number_input("Années crédit", value=20, min_value=0, max_value=100)

    # assurances
    st.header("Assurances")
    assurance_pno_annuel = st.number_input("Coût annuel de l'assurance PNO", value=100, min_value=0)
    assurance_gli_annuel = st.number_input("Coût annuel de l'assurance GLI", value=250, min_value=0)
    assurance_emprunteur_annuel = st.number_input("Coût annuel de l'assurance emprunteur", value=0, min_value=0)

    # preparation appartement
    st.header("Préparation de l'appartement")
    cout_plans = st.number_input("Coût des plans", value=0, min_value=0)
    cout_meubles = st.number_input("Coût des meubles", value=3000, min_value=0)
    cout_travaux = st.number_input("Coût des travaux", value=11583, min_value=0)

    # mise en location
    st.header("Mise en location")
    loyer_mensuel = st.number_input("Loyer mensuel (euros)", value=650)
    taux_occupation = st.number_input("Taux d'occupation (%)", value=90.0, min_value=0.0, max_value=100.0)
    frais_recherche_locataire = st.number_input("Frais de recherche du locataire", value=415, min_value=0)
    frais_gestion_taux = st.number_input("Frais de gestion locative (%)", value=6.5, min_value=0.0, max_value=100.0)

    # frais divers annuels
    st.header("Frais divers annuels")
    cout_expert_comptable = st.number_input("Coût de l'expert comptable annuel (euros)", value=200, min_value=0)
    petits_travaux_annuels = st.number_input("Petits travaux annuels (euros)", value=1000, min_value=0)

    # amortissements (LMNP)
    # st.header("Amortissements - LMNP")
    # annees_amortissement_bien = st.number_input("Années amortissement bien", value=25, min_value=0)
    # annees_amortissement_mobilier = st.number_input("Années amortissement mobilier", value=5, min_value=0)
    # annees_amortissement_travaux = st.number_input("Années amortissement travaux", value=20, min_value=0)


# outputs
prix_m2 = cout_bien/superficie
st.metric(label="Prix au m2", value=prix_m2)

frais_notaire_cout = cout_bien * frais_notaire / 100
frais_notaire_total = frais_notaire_cout + frais_promesse_vente

apport_partie_1 = honoraires_chasseur + frais_notaire_total + cout_plans + cout_meubles + cout_travaux
cout_banque = cout_bien

if inclure_honoraires:
    apport_partie_1 -= honoraires_chasseur
    cout_banque += honoraires_chasseur

if inclure_travaux:
    apport_partie_1 -= (cout_plans + cout_travaux)
    cout_banque += (cout_plans + cout_travaux)

if inclure_meubles:
    apport_partie_1 -= cout_meubles
    cout_banque += cout_meubles

apport_partie_2 = taux_apport * cout_banque / 100
apport_total = apport_partie_1 + apport_partie_2
cout_operation = cout_banque + apport_partie_1
st.metric(label="Coût de l'opération", value=cout_operation)
st.metric(label="Apport total", value=apport_total)

montant_emprunt = cout_banque - apport_partie_2

echeancier_df, remboursement_mensuel_credit = func.generate_echeancier(montant_emprunt,
                                                                       taux_emprunt_mensuel,
                                                                       annees_credit)
remboursement_annuel_credit = remboursement_mensuel_credit * 12

credit = remboursement_annuel_credit * annees_credit
interets = credit - montant_emprunt

st.metric(label="Mensualités crédit", value=remboursement_mensuel_credit)

loyer_annuel = loyer_mensuel * 12 * taux_occupation / 100

rendement_brut = loyer_annuel / cout_operation * 100
st.metric(label="Rendement brut", value="{} %".format(rendement_brut))

frais_gestion_annuel = frais_gestion_taux * loyer_annuel / 100
assurances_cout_annuel = assurance_pno_annuel + assurance_gli_annuel + assurance_emprunteur_annuel

depenses_annuelles_gestion_bien = (charges_copropriete + frais_gestion_annuel + cout_expert_comptable
                                   + assurances_cout_annuel + frais_recherche_locataire + petits_travaux_annuels)

charges_annuelles = depenses_annuelles_gestion_bien + taxe_fonciere + remboursement_annuel_credit

cout_annuel_total = charges_annuelles + apport_total / annees_credit

cash_flow = loyer_annuel - charges_annuelles
cash_flow_reel = loyer_annuel - cout_annuel_total
st.metric(label="Cash flow mensuel (sans inclusion  apport)", value=cash_flow/12)
st.metric(label="Cash flow annuel (sans apport)", value=cash_flow)
st.metric(label="Cash flow annuel (avec apport)", value=cash_flow_reel)


st.header("Echeancier emprunt")
st.table(echeancier_df)







