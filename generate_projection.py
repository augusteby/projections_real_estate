import pandas as pd
import itertools
import numpy as np
from tqdm import tqdm
import joblib
from constants import Projections, LMNP
import os


APPORTS_TAUX = [0.1]
TAUX_OCCUPATION = np.arange(0.7, 0.9, 0.1)
ECART_A_LA_MOYENNE_LOYER = np.arange(-0.1, 1, 0.1)
ECART_A_LA_MOYENNE_CHARGES_COPRO = np.arange(-0.2, 0.3, 0.1)
ECART_A_LA_MOYENNE_PRIX_M2_AVANT_TRAVAUX = np.arange(-0.5, 0.3, 0.1)
ANNEES_CREDIT_LIST = [20]
TAUX_INTERET = np.arange(0.012, 0.02, 0.005)
OFF_MARKET = [True, False]
VARIABLES_TO_COMBINE = [APPORTS_TAUX, TAUX_OCCUPATION, ECART_A_LA_MOYENNE_LOYER, ANNEES_CREDIT_LIST,
                        TAUX_INTERET, ECART_A_LA_MOYENNE_PRIX_M2_AVANT_TRAVAUX, ECART_A_LA_MOYENNE_CHARGES_COPRO,
                        OFF_MARKET]

# source taxe fonciere: https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
TAXE_FONCIERE_TAUX = {'reims':0.2926, 'saint_denis':0.2265, 'paris':0.0837, 'marseille': 0.2402,
                      'strasbourg': 0.2249, 'rennes':0.2576, 'tinqueux': 0.155, 'bezannes': 0.2277}
TAXE_FONCIERE = 380

PRIX_M2_MOYEN = {'reims': 2350, 'tinqueux': 2267, 'bezannes': 3164}
LOYER_M2_MOYEN = {'reims': 11, 'tinqueux': 12.6, 'bezannes': 12.4}

COUT_MEUBLES = 7500
COUT_TRAVAUX = 32000
COUT_PLAN = 2000


FRAIS_NOTAIRE_TAUX = 0.08
FRAIS_RECHERCHE_LOCATAIRE = 0
FRAIS_AGENCE_GESTION_TAUX = 0.05
HONORAIRES_IL_TAUX = 0.084

COUT_EXPERT_COMPTABLE_ANNUEL = 300
# source charges copro: https://www.meilleurecopro.com/charges-de-copropriete/
CHARGES_COPRO_M2_ANNUEL = {'reims': 19.3, 'tinqueux': 20}

CHARGES_COPRO_ANNUEL = 512


ASSURANCE_PNO_ANNUEL = 150 # assurance proprietaire non occupant (https://reassurez-moi.fr/guide/assurance-habitation/pno-tarif pour des ordres de grandeur)
ASSURANCE_GLI_ANNUEL_TAUX = 0.035 # assurance garantie loyes impayes (https://reassurez-moi.fr/guide/assurance-loyer-impaye/cout) en pourcentage du loyer annuel
ASSURANCE_EMPRUNTEUR_ANNUEL = 15*12

# Pour des ordres de grandeurs pour les amortissements: https://gerant-immo.com/guide/LMNP-amortissement
TAUX_AMORTISSEMENT_BIEN = 0.03
ANNEES_AMORTISSEMENT_MOBILIER = 5
ANNEES_AMORTISSEMENT_TRAVAUX = 10
AMORTISSEMENT_MOBILIER_ANNUEL = COUT_MEUBLES/ANNEES_AMORTISSEMENT_MOBILIER
AMORTISSEMENT_TRAVAUX_ANNUEL = COUT_TRAVAUX/ANNEES_AMORTISSEMENT_TRAVAUX


def get_projection_report(ville, superficie_bien_m2, prix_m2_moyen_zone=None, loyer_m2_moyen_zone=None):
    """
    Quelques hypotheses:
    * Regime LMNP reel
    * Pour simplifier, on ne s'interesse qu'a la premiere annee pour l'impot LMNP
        (on fait l'hypothese que les 5-15 annees suivantes
        donneront le meme resultat: imposable ou pas imposable)
    * On n'inclut pas les cout des meubles et le cout des travaux dans le cout du bien
    """
    TOUTES_COMBINAISONS = list(itertools.product(*VARIABLES_TO_COMBINE))


    projection_dic = {Projections.COUT_OPERATION: [],Projections.IS_OFF_MARKET: [],Projections.RENDEMENT_BRUT: [],
                      Projections.APPORT_BANQUE: [],
                      Projections.TAUX_INTERET: [], Projections.NB_ANNEES_EMPRUNT: [], Projections.LOYER_MENSUEL: [],
                      Projections.ECART_LOYER_MOYEN: [],
                      Projections.CASH_FLOW_ANNUEL: [], Projections.CASH_FLOW_ANNUEL_APPORT_TOTAL_INCLU: [],
                      Projections.DOIT_PAYER_IMPOT_PREMIERE_ANNEE: [],
                      Projections.LOYER_ANNUEL: [], Projections.CHARGES_ANNUELLES: [], Projections.TAUX_OCCUPATION: [],
                      Projections.APPORT_TOTAL: [],
                      Projections.ECART_PRIX_M2_MOYEN_AVANT: [], Projections.ECART_PRIX_M2_MOYEN_APRES: [],
                      Projections.PRIX_M2_AVANT: [], Projections.PRIX_M2_APRES: [], Projections.ECART_CHARGES_COPRO_MOYEN: [],
                      Projections.PREMIERE_ANNEE_IMPOSITION: []}


    all_compta_lmnp = []

    for combinaison in tqdm(TOUTES_COMBINAISONS):
        doit_payer_impot = False

        apport_taux_i = combinaison[0]
        taux_occupation_i = combinaison[1]
        ecart_au_loyer_moyen = combinaison[2]
        annees_credit = combinaison[3]
        taux_interet = combinaison[4]
        ecart_prix_m2_prix_moyen_avant = combinaison[5]
        ecart_aux_charges_copro_moyen = combinaison[6]
        off_market = combinaison[7]

        prix_m2_avant = (1 + ecart_prix_m2_prix_moyen_avant) * prix_m2_moyen_zone
        cout_bien = prix_m2_avant * superficie_bien_m2

        frais_notaire = cout_bien * FRAIS_NOTAIRE_TAUX
        amortissement_bien_annuel = TAUX_AMORTISSEMENT_BIEN * cout_bien
        amortissements_hors_bien = AMORTISSEMENT_MOBILIER_ANNUEL + AMORTISSEMENT_TRAVAUX_ANNUEL

        montant_empruntable = cout_bien + COUT_TRAVAUX + COUT_PLAN
        cout_sans_notaire = montant_empruntable + COUT_MEUBLES
        cout_avant_honoraires = cout_sans_notaire + frais_notaire
        if off_market:
            honoraires_il = 0
        else:
            honoraires_il = HONORAIRES_IL_TAUX * cout_avant_honoraires

        cout_operation = cout_avant_honoraires + honoraires_il

        prix_m2_apres = cout_sans_notaire / superficie_bien_m2
        ecart_prix_m2_prix_moyen_apres = (prix_m2_apres - prix_m2_moyen_zone) / prix_m2_moyen_zone

        apport_banque = apport_taux_i * montant_empruntable
        apport_total = COUT_MEUBLES + frais_notaire + apport_banque + honoraires_il

        # Calcul de mortgage
        montant_emprunt = montant_empruntable - apport_banque
        interet = taux_interet * montant_emprunt
        credit = montant_emprunt + interet
        remboursement_annuel_credit = credit / annees_credit

        # Calcul des revenus locatifs annuels a partir du rendement brut vise
        # et en prenant en compte le taux d'occupation
        loyer_mensuel = (1 + ecart_au_loyer_moyen) * loyer_m2_moyen_zone * superficie_bien_m2
        loyer_annuel_theorique = loyer_mensuel * 12
        loyer_annuel_percu = loyer_annuel_theorique * taux_occupation_i
        rendement_brut = loyer_annuel_theorique / cout_operation

        frais_gestion_annuel = FRAIS_AGENCE_GESTION_TAUX * loyer_annuel_theorique

        # Calcul de la taxe fonciere selon:
        # https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
        # On applique la taxe fonciere definie pour la commune a 50% de la totalite
        # du loyer annuel theorique car il s'agit ici d'une propriete batie
        taxe_fonciere = TAXE_FONCIERE

        assurance_gli_annuelle = ASSURANCE_GLI_ANNUEL_TAUX*loyer_annuel_theorique
        cout_assurances_annuel = ASSURANCE_PNO_ANNUEL + assurance_gli_annuelle + ASSURANCE_EMPRUNTEUR_ANNUEL

        # charges_copro_annuel = (1 + ecart_aux_charges_copro_moyen) * CHARGES_COPRO_M2_ANNUEL[ville] * superficie_bien_m2
        charges_copro_annuel = CHARGES_COPRO_ANNUEL
        depenses_annuelles_gestion_bien = (charges_copro_annuel + frais_gestion_annuel + COUT_EXPERT_COMPTABLE_ANNUEL
                                           + cout_assurances_annuel + FRAIS_RECHERCHE_LOCATAIRE)

        charges_annuel_avant_remboursement_credit = depenses_annuelles_gestion_bien + taxe_fonciere
        charges_annuel = charges_annuel_avant_remboursement_credit + remboursement_annuel_credit

        first_year_of_imposition, compta_par_an = get_fiscalite_lmnp_par_an(annees_credit, loyer_annuel_percu,
                                                                            amortissement_bien_annuel,
                                                                            amortissements_hors_bien,
                                                                            charges_annuel_avant_remboursement_credit,
                                                                            frais_notaire, interet)
        all_compta_lmnp.append(compta_par_an)

        # Pour les couts annuels, on ajoute les frais de notaire et l'apport ammortis sur la duree
        # du pret
        couts_annuel_total = charges_annuel + apport_total / annees_credit

        # On ne s'interesse qu'a la premiere annee. Pour simplifier, on fait l'hypothese que
        # la valeur de la variable doit_payer_impot restera la meme pour de nombreuses annees ensuite
        if first_year_of_imposition == 1:
            doit_payer_impot = True
            #TODO generer la projection dans le cas ou l'impot est dû
        else:
            cash_flow = loyer_annuel_percu - charges_annuel
            cash_flow_total = loyer_annuel_percu - couts_annuel_total

            projection_dic[Projections.COUT_OPERATION].append(cout_operation)
            projection_dic[Projections.IS_OFF_MARKET].append(off_market)
            projection_dic[Projections.RENDEMENT_BRUT].append(rendement_brut)
            projection_dic[Projections.APPORT_BANQUE].append(apport_taux_i)
            projection_dic[Projections.TAUX_INTERET].append(taux_interet)
            projection_dic[Projections.NB_ANNEES_EMPRUNT].append(annees_credit)
            projection_dic[Projections.LOYER_MENSUEL].append(loyer_mensuel)
            projection_dic[Projections.ECART_LOYER_MOYEN].append(ecart_au_loyer_moyen)
            projection_dic[Projections.CASH_FLOW_ANNUEL].append(cash_flow)
            projection_dic[Projections.CASH_FLOW_ANNUEL_APPORT_TOTAL_INCLU].append(cash_flow_total)
            projection_dic[Projections.DOIT_PAYER_IMPOT_PREMIERE_ANNEE].append(doit_payer_impot)
            projection_dic[Projections.LOYER_ANNUEL].append(loyer_annuel_percu)
            projection_dic[Projections.CHARGES_ANNUELLES].append(charges_annuel)
            projection_dic[Projections.TAUX_OCCUPATION].append(taux_occupation_i)
            projection_dic[Projections.APPORT_TOTAL].append(apport_total)
            projection_dic[Projections.ECART_PRIX_M2_MOYEN_AVANT].append(ecart_prix_m2_prix_moyen_avant)
            projection_dic[Projections.ECART_PRIX_M2_MOYEN_APRES].append(ecart_prix_m2_prix_moyen_apres)
            projection_dic[Projections.PRIX_M2_AVANT].append(prix_m2_avant)
            projection_dic[Projections.PRIX_M2_APRES].append(prix_m2_apres)
            projection_dic[Projections.ECART_CHARGES_COPRO_MOYEN].append(ecart_aux_charges_copro_moyen)
            projection_dic[Projections.PREMIERE_ANNEE_IMPOSITION].append(first_year_of_imposition)

    projection_df = pd.DataFrame(projection_dic)

    return projection_df, all_compta_lmnp

def get_fiscalite_lmnp_par_an(annees_credit, loyer_annuel_percu, amortissement_bien_annuel, amortissements_hors_bien,
                              charges_annuel_avant_remboursement_credit, frais_notaire, interet):
    """
    Sources:
    https://www.smartloc.fr/blog/fiscalite-de-location-meublee-regime-reel-en-lmnp/

    https://www.legifrance.gouv.fr/codes/id/LEGIARTI000006302900/2008-05-01/

    Quelques regles:
    * L'amortissement du bien ne peut creer un deficit ou l'augmenter si il existe deja suite aux imputations des
        depenses reelles (charges directes ou travaux amortis)
    * Il est possible de creer un deficit a partir des seules depenses reelles
    * Un deficit sur une annee (qui ne peut etre cree que par des depenses reelles) peut etre reporte sur les exercices
        suivants dans la limite de 10 ans
    * La part non utilisee de l'amortissement du bien peut etre reporte indefiniment

    Args:
        annees_credit:
        loyer_annuel_percu:
        amortissement_bien_annuel:
        amortissements_hors_bien:
        charges_annuel_avant_remboursement_credit:
        frais_notaire:
        interet:


    Returns:

    """
    compta_par_an = {}

    first_year_of_imposition = 0

    deficit_memory = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 0}

    for i in range(1, annees_credit+1):
        compta_annee_i = {}

        compta_annee_i[Projections.LOYER_ANNUEL] = loyer_annuel_percu

        # La premiere annee, on peut ajouter les frais de notaire aux charges
        # TODO confirmer que l'on puisse aussi ajouter la totalite des interets aux charges la premiere annee
        if i == 1:
            charges_avant_amort_bien =  (amortissements_hors_bien + charges_annuel_avant_remboursement_credit
                                         + frais_notaire + interet)
            report = 0
        else:
            charges_avant_amort_bien = amortissements_hors_bien + charges_annuel_avant_remboursement_credit
            report = 0
            deficit_memory = get_one_year_older_deficit_memory(deficit_memory)

        charges_apres_amort_bien = charges_avant_amort_bien + amortissement_bien_annuel

        revenus_imposables_avant_amort_bien = loyer_annuel_percu - charges_avant_amort_bien

        revenus_imposables_apres_amort_bien = loyer_annuel_percu - charges_apres_amort_bien

        # si il existe deja un deficit avant la prise en compte de l'amortissement du bien, ou si la prise en compte
        # de l'amortissement du bien engendre un deficit, alors on reporte l'amortissement du bien a l'annee d'apres
        if revenus_imposables_avant_amort_bien < 0:
            deficit_depenses_reelles = np.abs(revenus_imposables_avant_amort_bien)
            report += amortissement_bien_annuel + deficit_depenses_reelles
            compta_annee_i[LMNP.CHARGES_TOTALES] = charges_avant_amort_bien
            compta_annee_i[LMNP.REVENUS_IMPOSABLES] = 0
            compta_annee_i[LMNP.IS_AMORTISSEMENT_BIEN_REPORTE] = True
            compta_annee_i[LMNP.IS_IMPOSABLE] = False
            compta_annee_i[LMNP.VALEUR_TOTAL_REPORT] = report
            deficit_memory[i] = {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: deficit_depenses_reelles,
                                 LMNP.ANNEES_RESTANTES: 10}
            deficit_memory[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] += amortissement_bien_annuel
            compta_annee_i[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] = deficit_memory[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN]
        elif revenus_imposables_avant_amort_bien >= 0 and revenus_imposables_apres_amort_bien < 0:
            deficit_depenses_reelles = 0
            report += amortissement_bien_annuel + deficit_depenses_reelles
            compta_annee_i[LMNP.CHARGES_TOTALES] = charges_avant_amort_bien
            compta_annee_i[LMNP.REVENUS_IMPOSABLES], deficit_memory = get_revenus_imposables_apres_utilisation_deficit_reporte(
                revenus_imposables_avant_amort_bien, deficit_memory)
            compta_annee_i[LMNP.IS_AMORTISSEMENT_BIEN_REPORTE] = True
            compta_annee_i[LMNP.IS_IMPOSABLE] = False
            compta_annee_i[LMNP.VALEUR_TOTAL_REPORT] = report
            deficit_memory[i] = {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: deficit_depenses_reelles,
                                 LMNP.ANNEES_RESTANTES: 0}
            deficit_memory[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] += amortissement_bien_annuel
            compta_annee_i[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] = deficit_memory[
                LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN]
        elif revenus_imposables_avant_amort_bien >= 0 and revenus_imposables_apres_amort_bien >= 0:
            if first_year_of_imposition == 0:
                first_year_of_imposition = i
            compta_annee_i[LMNP.CHARGES_TOTALES] = charges_apres_amort_bien
            compta_annee_i[LMNP.REVENUS_IMPOSABLES], deficit_memory = get_revenus_imposables_apres_utilisation_deficit_reporte(
                revenus_imposables_apres_amort_bien, deficit_memory)
            compta_annee_i[LMNP.IS_AMORTISSEMENT_BIEN_REPORTE] = False
            compta_annee_i[LMNP.IS_IMPOSABLE] = True
            compta_annee_i[LMNP.VALEUR_TOTAL_REPORT] = report
            compta_annee_i[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] = deficit_memory[
                LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN]

        compta_par_an[i] = compta_annee_i

    return first_year_of_imposition, compta_par_an

def get_revenus_imposables_apres_utilisation_deficit_reporte(revenus_imposables_avant_utilisation_deficit,
                                                             memoire_des_deficites):
    revenus_imposables_apres_utilisation_deficit = revenus_imposables_avant_utilisation_deficit
    if revenus_imposables_avant_utilisation_deficit <= 0:
        return 0, memoire_des_deficites
    else:
        # Enlever les deficit sur les depenses reelles reportes annee par annee
        for year_i in memoire_des_deficites:
            if year_i != LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN and memoire_des_deficites[year_i][LMNP.ANNEES_RESTANTES] > 0:
                diff1 = revenus_imposables_apres_utilisation_deficit - memoire_des_deficites[year_i][LMNP.DEFICIT_RESTANT_DEPENSES_REELLES]
                if diff1 >= 0:
                    revenus_imposables_apres_utilisation_deficit -= memoire_des_deficites[year_i][LMNP.DEFICIT_RESTANT_DEPENSES_REELLES]
                    memoire_des_deficites[year_i][LMNP.DEFICIT_RESTANT_DEPENSES_REELLES] = 0
                else:
                    revenus_imposables_apres_utilisation_deficit = 0
                    memoire_des_deficites[year_i][LMNP.DEFICIT_RESTANT_DEPENSES_REELLES] = np.abs(diff1)
                    break

        # Si apres le retrait de tous les deficit sur les depenses reelles, le revenu imposable est toujours positif, enlever
        # le deficit cumule lie a l'amortissement du bien
        if revenus_imposables_apres_utilisation_deficit > 0 and memoire_des_deficites[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] > 0:
            diff2 = revenus_imposables_apres_utilisation_deficit - memoire_des_deficites[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN]

            if diff2 >= 0:
                revenus_imposables_apres_utilisation_deficit -= memoire_des_deficites[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN]
                memoire_des_deficites[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] = 0
            else:
                revenus_imposables_apres_utilisation_deficit = 0
                memoire_des_deficites[LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN] = np.abs(diff2)

        return revenus_imposables_apres_utilisation_deficit, memoire_des_deficites

def get_one_year_older_deficit_memory(deficit_memory):
    for key in deficit_memory:
        if type(key) == int and deficit_memory[key][LMNP.ANNEES_RESTANTES] > 0:
            deficit_memory[key][LMNP.ANNEES_RESTANTES] -= 1

    return deficit_memory




if __name__=='__main__':
    ville = 'reims'
    superficie_bien_m2 = 38
    prix_m2_moyen_zone = PRIX_M2_MOYEN[ville]
    loyer_m2_moyen_zone = LOYER_M2_MOYEN[ville]

    projection_df, all_compta_par_an = get_projection_report(ville, superficie_bien_m2, prix_m2_moyen_zone, loyer_m2_moyen_zone)
    projection_df_cash_flow_pos = projection_df[projection_df[Projections.CASH_FLOW_ANNUEL]>=0]
    print(projection_df_cash_flow_pos)

    result_storage_folder = os.path.join('results', 'projection_report_{}_{}'.format(ville, superficie_bien_m2))
    os.makedirs(result_storage_folder, exist_ok=True)
    projection_report_results_filepath = os.path.join(result_storage_folder, 'projection_report_all.csv')
    projection_df.to_csv(projection_report_results_filepath, index=False)
    projection_df_cash_flow_pos.to_csv('projection_report_cash_flow_pos.csv', index=False)
    print('Rapport de projection genere pour un bien à {} avec une superficie de {} m2'
          ' dans une zone ou le prix au m2 moyen est de {} euros et le loyer au m2 '
          'moyen est de {} euros'.format(ville, superficie_bien_m2, prix_m2_moyen_zone, loyer_m2_moyen_zone))

    ids_to_keep_compta = projection_df_cash_flow_pos.index.values
    all_compta_par_an_pos = np.array(all_compta_par_an)[ids_to_keep_compta]
    for k in range(len(all_compta_par_an_pos)):
        compta_par_an = all_compta_par_an_pos[k]
        fiscalite_lmnp_df = pd.DataFrame(compta_par_an)
        fiscalite_lmnp_results_filepath = os.path.join(result_storage_folder, 'fiscalite_lmnp_{}.csv'.format(k))
        fiscalite_lmnp_df.to_csv(fiscalite_lmnp_results_filepath)
