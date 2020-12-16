import unittest

from constants import LMNP

from generate_projection import get_revenus_imposables_apres_utilisation_deficit_reporte, get_one_year_older_deficit_memory


class TestGenerationProjection(unittest.TestCase):
    def setUp(self):
        pass

    # def test_get_fiscalite_lmnp_par_an(self):
    #     annees_credit = 4
    #     loyer_annuel_percu = 1000
    #     amortissement_bien_annuel = 100
    #     amortissements_hors_bien = 100
    #     charges_annuel_avant_remboursement_credit = 1000
    #     frais_notaire = 500
    #     interet = 500

    def test_get_revenus_imposables_apres_utilisation_deficit_reporte(self):
        test_revenus_imposables_avant_utilisation_deficit = 1250

        # Scenario 1
        test_memoire_des_deficites_1 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 2},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 3},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 4}}

        expected_revenus_imposables_apres_utilisation_deficit_1 = 150
        expected_memoire_des_deficites_1 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 0,
                                            1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 2},
                                            2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 3},
                                            3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 4}}

        test_revenus_imposables_apres_utilisation_deficit_1, test_memoire_des_deficites_1 = get_revenus_imposables_apres_utilisation_deficit_reporte(
            test_revenus_imposables_avant_utilisation_deficit, test_memoire_des_deficites_1)

        self.assertEqual(expected_revenus_imposables_apres_utilisation_deficit_1,
                         test_revenus_imposables_apres_utilisation_deficit_1)
        self.assertEqual(expected_memoire_des_deficites_1, test_memoire_des_deficites_1)

        # Scenario 2
        test_memoire_des_deficites_2 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 800,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 2},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 3},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 200,
                                            LMNP.ANNEES_RESTANTES: 4}}

        expected_revenus_imposables_apres_utilisation_deficit_2 = 0
        expected_memoire_des_deficites_2 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 150,
                                            1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 2},
                                            2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 3},
                                            3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 4}}

        test_revenus_imposables_apres_utilisation_deficit_2, test_memoire_des_deficites_2 = get_revenus_imposables_apres_utilisation_deficit_reporte(
            test_revenus_imposables_avant_utilisation_deficit, test_memoire_des_deficites_2)

        self.assertEqual(expected_revenus_imposables_apres_utilisation_deficit_2,
                         test_revenus_imposables_apres_utilisation_deficit_2)
        self.assertEqual(expected_memoire_des_deficites_2, test_memoire_des_deficites_2)

        # Scenario 3
        test_memoire_des_deficites_3 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 2},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 3},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 4}}

        expected_revenus_imposables_apres_utilisation_deficit_3 = 0
        expected_memoire_des_deficites_3 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                            1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 2},
                                            2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 3},
                                            3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 250,
                                                LMNP.ANNEES_RESTANTES: 4}}

        test_revenus_imposables_apres_utilisation_deficit_3, test_memoire_des_deficites_3 = get_revenus_imposables_apres_utilisation_deficit_reporte(
            test_revenus_imposables_avant_utilisation_deficit, test_memoire_des_deficites_3)

        self.assertEqual(expected_revenus_imposables_apres_utilisation_deficit_3,
                         test_revenus_imposables_apres_utilisation_deficit_3)
        self.assertEqual(expected_memoire_des_deficites_3, test_memoire_des_deficites_3)

        # Scenario 4
        test_memoire_des_deficites_4 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 0},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 3},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 4}}

        expected_revenus_imposables_apres_utilisation_deficit_4 = 0
        expected_memoire_des_deficites_4 = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 250,
                                            1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                                LMNP.ANNEES_RESTANTES: 0},
                                            2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 3},
                                            3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 0,
                                                LMNP.ANNEES_RESTANTES: 4}}

        test_revenus_imposables_apres_utilisation_deficit_4, test_memoire_des_deficites_4 = get_revenus_imposables_apres_utilisation_deficit_reporte(
            test_revenus_imposables_avant_utilisation_deficit, test_memoire_des_deficites_4)

        self.assertEqual(expected_revenus_imposables_apres_utilisation_deficit_4,
                         test_revenus_imposables_apres_utilisation_deficit_4)
        self.assertEqual(expected_memoire_des_deficites_4, test_memoire_des_deficites_4)

    def test_get_one_year_older_deficit_memory(self):

        input_memoire_des_deficites = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 1},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 0},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 4}}

        expected_test_memoire_des_deficites = {LMNP.DEFICIT_RESTANT_AMORTISSEMENT_BIEN: 500,
                                        1: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 0},
                                        2: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 0},
                                        3: {LMNP.DEFICIT_RESTANT_DEPENSES_REELLES: 500,
                                            LMNP.ANNEES_RESTANTES: 3}}

        output_memoire_des_deficites = get_one_year_older_deficit_memory(input_memoire_des_deficites)

        self.assertEqual(expected_test_memoire_des_deficites, output_memoire_des_deficites)
