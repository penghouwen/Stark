from lib.test.evaluation.environment import EnvSettings

def local_env_settings():
    settings = EnvSettings()

    # Set your local paths here.

    settings.davis_dir = ''
    settings.got10k_lmdb_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/got10k_lmdb'
    settings.got10k_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/got10k'
    settings.got_packed_results_path = ''
    settings.got_reports_path = ''
    settings.lasot_lmdb_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/lasot_lmdb'
    settings.lasot_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/lasot'
    settings.network_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/test/networks'    # Where tracking networks are stored.
    settings.nfs_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/nfs'
    settings.otb_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/OTB2015'
    settings.prj_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr'
    settings.result_plot_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/test/result_plots'
    settings.results_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/test/tracking_results'    # Where to store tracking results
    settings.save_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr'
    settings.segmentation_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/test/segmentation_results'
    settings.tc128_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/TC128'
    settings.tn_packed_results_path = ''
    settings.tpl_path = ''
    settings.trackingnet_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/trackingNet'
    settings.uav_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/UAV123'
    settings.vot_path = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/VOT2019'
    settings.youtubevos_dir = ''

    return settings

