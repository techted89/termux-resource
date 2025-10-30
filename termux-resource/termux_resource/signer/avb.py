import subprocess

def sign_vbmeta(vbmeta_path, key_path, algorithm, output_path, include_images):
    """
    Signs a vbmeta.img file.
    """
    # Get the absolute path to the avbtool.py script
    import os
    script_dir = os.path.dirname(os.path.realpath(__file__))
    avbtool_path = os.path.join(script_dir, '..', '..', 'third_party', 'avbtool.py')

    cmd = [
        'python3',
        avbtool_path,
        'make_vbmeta_image',
        '--output', output_path,
        '--key', key_path,
        '--algorithm', algorithm,
    ]
    for image in include_images:
        cmd.extend(['--include_descriptors_from_image', image])

    subprocess.run(cmd, check=True)
