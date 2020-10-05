#!/usr/bin/env python3
""" experiment running script for training data generation
"""

import os
import subprocess

SETUP_DIRECTORIES = True
GENERATE_GEO_TOY = False
GENERATE_SPIDER = True
DEV = True

subprocess.call(['export', 'PYTHONPATH="${PYTHONPATH}:$(pwd)"'], shell=True)

# create directory structure
if SETUP_DIRECTORIES:
    if not os.path.exists('logs'):
        os.makedirs('logs')
    if not os.path.exists('data'):
        os.makedirs('data')

# generate geo toy data (for development)
if GENERATE_GEO_TOY:
    subprocess.call(['python', 'generation/generate.py',
                     '-db', 'geo',
                     '-toy',
                     '-rand_drop_scale', '3',
                     '-pp_scale', '3',
                     '-validate'])

# generate training data for each spider db separately
if GENERATE_SPIDER:
    if DEV:
        dirs = ['battle_death', 'car_1', 'concert_singer', 'course_teach', 'cre_Doc_Template_Mgt', 'dog_kennels',
                'employee_hire_evaluation', 'flight_2', 'museum_visit', 'network_1', 'orchestra', 'pets_1',
                'poker_player', 'real_estate_properties', 'singer', 'student_transcripts_tracking', 'tvshow', 'voter_1',
                'world_1', 'wta_1']

        # dirs = ['voter_1', 'course_teach', 'pets_1', 'tvshow', 'car_1']

    else:
        # dirs = os.listdir('data/spider/database')
        # dirs.sort()

        dirs = ['academic', 'activity_1', 'aircraft', 'allergy_1', 'apartment_rentals',
                'architecture',
                'assets_maintenance', 'baseball_1', 'behavior_monitoring', 'bike_1', 'body_builder', 'book_2',
                'browser_web', 'candidate_poll', 'chinook_1', 'cinema', 'city_record', 'climbing', 'club_1',
                'coffee_shop', 'college_1', 'college_2', 'college_3', 'company_1', 'company_employee', 'company_office',
                'county_public_safety', 'cre_Doc_Control_Systems', 'cre_Doc_Tracking_DB', 'cre_Docs_and_Epenses',
                'cre_Drama_Workshop_Groups', 'cre_Theme_park', 'csu_1', 'culture_company', 'customer_complaints',
                'customer_deliveries', 'customers_and_addresses', 'customers_and_invoices',
                'customers_and_products_contacts', 'customers_campaigns_ecommerce', 'customers_card_transactions',
                'debate', 'decoration_competition', 'department_management', 'department_store', 'device',
                'document_management', 'dorm_1', 'driving_school', 'e_government', 'e_learning', 'election',
                'election_representative', 'entertainment_awards', 'entrepreneur', 'epinions_1', 'farm', 'film_rank',
                'flight_1', 'flight_4', 'flight_company', 'formula_1', 'game_1', 'game_injury', 'gas_company', 'geo',
                'gymnast', 'hospital_1', 'hr_1', 'icfp_1', 'imdb', 'inn_1', 'insurance_and_eClaims', 'insurance_fnol',
                'insurance_policies', 'journal_committee', 'loan_1', 'local_govt_and_lot', 'local_govt_in_alabama',
                'local_govt_mdm', 'machine_repair', 'manufactory_1', 'manufacturer', 'match_season',
                'medicine_enzyme_interaction', 'mountain_photos', 'movie_1', 'music_1', 'music_2', 'music_4', 'musical',
                'network_2', 'news_report', 'party_host', 'party_people', 'performance_attendance', 'perpetrator',
                'phone_1', 'phone_market', 'pilot_record', 'product_catalog', 'products_for_hire',
                'products_gen_characteristics', 'program_share', 'protein_institute', 'race_track', 'railway',
                'restaurant_1', 'restaurants', 'riding_club', 'roller_coaster', 'sakila_1', 'scholar', 'school_bus',
                'school_finance', 'chool_player', 'scientist_1', 'ship_1', 'ship_mission', 'shop_membership',
                'small_bank_1', 'soccer_1', 'soccer_2', 'solvency_ii', 'sports_competition', 'station_weather',
                'store_1', 'store_product', 'storm_record', 'student_1', 'student_assessment', 'swimming',
                'theme_gallery', 'tracking_grants_for_research', 'tracking_orders', 'tracking_share_transactions',
                'tracking_software_problems', 'train_station', 'twitter_1', 'university_basketball', 'voter_2',
                'wedding', 'wine_1', 'workshop_paper', 'wrestler', 'yelp']

    counts = ['50', '500']
    template_files = ['templates']
    ppdbs = ['ppdb']
    group_bool = [True, False]
    join_bool = [True, False]
    pp_scales = ['0', '3', '6']
    drop_scales = ['0', '3', '6']
    adj_scales = ['0', '3', '6']

    rename = []

    for count in counts:
        for db in dirs:
            processes = []
            for templates in template_files:
                for ppdb in ppdbs:
                    for join in join_bool:
                        for group in group_bool:
                            for pp in pp_scales:
                                if pp == 0 and ppdb != ppdbs[0]:
                                    continue
                                for drop in drop_scales:
                                    for adj in adj_scales:
                                        if (not (group and join)) and (not (pp == drop == adj == '0')):
                                            continue
                                        out_dir = 'data/spider/synthetic'
                                        out_dir += '/dev' if DEV else '/train'
                                        out_dir += f'/{count}'
                                        out_dir += f'/{db}_{templates}_{ppdb}_j{join}_g{group}_p{pp}_d{drop}_a{adj}/'
                                        if not os.path.exists(out_dir + 'train.json'):
                                            if not os.path.exists(out_dir):
                                                os.makedirs(out_dir)
                                            print(out_dir)
                                            call = ['time', '-p',  # time generation
                                                    'python', 'generation/generate.py',
                                                    '-db', db,
                                                    '-out_dir', out_dir,
                                                    '-query_bound', count,
                                                    '-validation_split', '0.1',
                                                    '-templates', 'data/' + templates + '.txt',
                                                    '-ppdb_file', 'data/ppdb/' + ppdb + '.json',
                                                    '-rand_drop_scale', drop,
                                                    '-pp_scale', pp,
                                                    '-adjective_scale', adj]
                                            if not group:
                                                call.append('-no_group_by')
                                            if not join:
                                                call.append('-no_join')
                                            with open(out_dir + '/time.txt', 'w') as out:
                                                processes.append(subprocess.Popen(call, stdout=out, stderr=out))
                                            rename.append((f'{out_dir}dev.json', f'{out_dir}dev_synth.json'))

            for p in processes:
                p.wait()
            for pair in rename:
                subprocess.call(['mv', pair[0], pair[1]])
            rename = []
            for templates in template_files:
                for ppdb in ppdbs:
                    for join in join_bool:
                        for group in group_bool:
                            for pp in pp_scales:
                                if pp == 0 and ppdb != ppdbs[0]:
                                    continue
                                for drop in drop_scales:
                                    for adj in adj_scales:
                                        if (not (group and join)) and (not (pp == drop == adj == '0')):
                                            continue
                                        out_dir = 'data/spider/synthetic'
                                        out_dir += '/dev' if DEV else '/train'
                                        out_dir += f'/{count}'
                                        out_dir += f'/{db}_{templates}_{ppdb}_j{join}_g{group}_p{pp}_d{drop}_a{adj}/'

                                        if not os.path.exists(f'{out_dir}database'):
                                            subprocess.call(['ln', '-s', '../database', f'{out_dir}database'])
                                        if not os.path.exists(f'{out_dir}tables.json'):
                                            subprocess.call(['ln', '-s', f'../tables.json', f'{out_dir}tables.json'])
                                        subprocess.call(['cp', f'/home/ngeisler/data/spider/filtered/dev_canon/{db}/dev.json', f'{out_dir}dev.json'])
                                        subprocess.call(['python', 'helper_scripts/transform_gold.py', f'{out_dir}dev.json'])
                                        subprocess.call(['python', 'helper_scripts/transform_gold.py', f'{out_dir}train.json'])
                                        subprocess.call(['python', 'helper_scripts/transform_gold.py', f'{out_dir}dev_synth.json'])
