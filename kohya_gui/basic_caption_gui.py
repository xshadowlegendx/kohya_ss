import gradio as gr
from easygui import msgbox
import subprocess
from .common_gui import get_folder_path, add_pre_postfix, find_replace, scriptdir, list_dirs
import os
import sys

from .custom_logging import setup_logging

# Set up logging
log = setup_logging()

PYTHON = sys.executable

def caption_images(
    caption_text,
    images_dir,
    overwrite,
    caption_ext,
    prefix,
    postfix,
    find_text,
    replace_text,
):
    # Check if images_dir is provided
    if not images_dir:
        msgbox(
            'Image folder is missing. Please provide the directory containing the images to caption.'
        )
        return

    # Check if caption_ext is provided
    if not caption_ext:
        msgbox('Please provide an extension for the caption files.')
        return

    if caption_text:
        log.info(f'Captioning files in {images_dir} with {caption_text}...')

        # Build the command to run caption.py
        run_cmd = fr'{PYTHON} "{scriptdir}/tools/caption.py"'
        run_cmd += f' --caption_text="{caption_text}"'

        # Add optional flags to the command
        if overwrite:
            run_cmd += f' --overwrite'
        if caption_ext:
            run_cmd += f' --caption_file_ext="{caption_ext}"'

        run_cmd += f' "{images_dir}"'

        log.info(run_cmd)

        env = os.environ.copy()
        env['PYTHONPATH'] = fr"{scriptdir}{os.pathsep}{scriptdir}/tools{os.pathsep}{env.get('PYTHONPATH', '')}"

        # Run the command based on the operating system
        subprocess.run(run_cmd, shell=True, env=env)

    # Check if overwrite option is enabled
    if overwrite:
        if prefix or postfix:
            # Add prefix and postfix to caption files
            add_pre_postfix(
                folder=images_dir,
                caption_file_ext=caption_ext,
                prefix=prefix,
                postfix=postfix,
            )
        if find_text:
            # Find and replace text in caption files
            find_replace(
                folder_path=images_dir,
                caption_file_ext=caption_ext,
                search_text=find_text,
                replace_text=replace_text,
            )
    else:
        if prefix or postfix:
            # Show a message if modification is not possible without overwrite option enabled
            msgbox(
                'Could not modify caption files with requested change because the "Overwrite existing captions in folder" option is not selected.'
            )

    log.info('Captioning done.')


# Gradio UI
def gradio_basic_caption_gui_tab(headless=False, default_images_dir=None):
    from .common_gui import create_refresh_button

    # Set default images directory if not provided
    default_images_dir = default_images_dir if default_images_dir is not None else os.path.join(scriptdir, "data")
    current_images_dir = default_images_dir

    # Function to list directories
    def list_images_dirs(path):
        # Allows list_images_dirs to modify current_images_dir outside of this function
        nonlocal current_images_dir
        current_images_dir = path
        return list(list_dirs(path))

    # Gradio tab for basic captioning
    with gr.Tab('Basic Captioning'):
        # Markdown description
        gr.Markdown(
            'This utility allows you to create simple caption files for each image in a folder.'
        )
        # Group and row for image folder selection
        with gr.Group(), gr.Row():
            # Dropdown for image folder
            images_dir = gr.Dropdown(
                label='Image folder to caption (containing the images to caption)',
                choices=[""] + list_images_dirs(default_images_dir),
                value="",
                interactive=True,
                allow_custom_value=True,
            )
            # Refresh button for image folder
            create_refresh_button(images_dir, lambda: None, lambda: {"choices": list_images_dirs(current_images_dir)},"open_folder_small")
            # Button to open folder
            folder_button = gr.Button(
                '📂', elem_id='open_folder_small', elem_classes=["tool"], visible=(not headless)
            )
            # Event handler for button click
            folder_button.click(
                get_folder_path,
                outputs=images_dir,
                show_progress=False,
            )
            # Textbox for caption file extension
            caption_ext = gr.Textbox(
                label='Caption file extension',
                placeholder='Extension for caption file (e.g., .caption, .txt)',
                value='.txt',
                interactive=True,
            )
            # Checkbox to overwrite existing captions
            overwrite = gr.Checkbox(
                label='Overwrite existing captions in folder',
                interactive=True,
                value=False,
            )
        # Row for caption prefix and text
        with gr.Row():
            # Textbox for caption prefix
            prefix = gr.Textbox(
                label='Prefix to add to caption',
                placeholder='(Optional)',
                interactive=True,
            )
            # Textbox for caption text
            caption_text = gr.Textbox(
                label='Caption text',
                placeholder='e.g., "by some artist". Leave empty if you only want to add a prefix or postfix.',
                interactive=True,
                lines=2,
            )
            # Textbox for caption postfix
            postfix = gr.Textbox(
                label='Postfix to add to caption',
                placeholder='(Optional)',
                interactive=True,
            )
        # Group and row for find and replace text
        with gr.Group(), gr.Row():
            # Textbox for find text
            find_text = gr.Textbox(
                label='Find text',
                placeholder='e.g., "by some artist". Leave empty if you only want to add a prefix or postfix.',
                interactive=True,
                lines=2,
            )
            # Textbox for replace text
            replace_text = gr.Textbox(
                label='Replacement text',
                placeholder='e.g., "by some artist". Leave empty if you want to replace with nothing.',
                interactive=True,
                lines=2,
            )
            # Button to caption images
            caption_button = gr.Button('Caption images')
            # Event handler for button click
            caption_button.click(
                caption_images,
                inputs=[
                    caption_text,
                    images_dir,
                    overwrite,
                    caption_ext,
                    prefix,
                    postfix,
                    find_text,
                    replace_text,
                ],
                show_progress=False,
            )

        # Event handler for dynamic update of dropdown choices
        images_dir.change(
            fn=lambda path: gr.Dropdown().update(choices=[""] + list_images_dirs(path)),
            inputs=images_dir,
            outputs=images_dir,
            show_progress=False,
        )
