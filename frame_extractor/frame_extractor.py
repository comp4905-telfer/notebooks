import ipywidgets as widgets
import os
import cv2
import matplotlib.pyplot as plt

from IPython.display import display, HTML, clear_output
from ipywidgets import Layout, HBox, VBox, Label, Text, Output, Button, Play, IntSlider, IntText
        
class VideoReader:
    def __init__(self, file, frame_step):
        self.file = file
        self.frame_step = frame_step
        self.cap = cv2.VideoCapture(file)
        self.FPS = self.cap.get(cv2.CAP_PROP_FPS)
        self.frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.name = os.path.splitext(os.path.split(self.file)[1])[0]
        self.current_index = 0
        self.current_frame = None
        
    def get_frame(self, index=None):
        if index is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.cap.read()
        self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.current_index = int(index or self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return self.current_frame
    
def validate_path(change):
    '''
    Paths are in red if they aren't valid
    '''
    if (str(change.new) == ''):
        change.owner.remove_class('invalid-path')
        return
    if not os.path.exists(str(change.new)):
        change.owner.add_class('invalid-path')
    else:
        change.owner.remove_class('invalid-path')
        
    
labeled_cap = None
unlabeled_cap = None
    
def run(labeled_path_initial_value = None, unlabeled_path_initial_value = None, save_path_initial_value = None):
    frame_step = 48 # how many frames to skip when using the play widget
    
    fluid = Layout(width='100%')
    auto_width = Layout(width='auto')
    flex_grow = Layout(flex='1 1 auto')
    
    labeled_video_path = Text(placeholder='/path/to/labeled-video', value=labeled_path_initial_value, layout=auto_width)
    unlabeled_video_path = Text(placeholder='/path/to/unlabeled-video', value=unlabeled_path_initial_value, layout=auto_width)
    load_videos = Button(description='Load')
    labeled_plot = Output(layout=Layout(flex='1 0 auto', border='1px solid black'))
    unlabeled_plot = Output(layout=Layout(flex='1 0 auto', border='1px solid black'))
    save_button = Button(description='Save')
    save_path = Text(placeholder='/save/path/', value=save_path_initial_value, layout=flex_grow)
    save_to = Output()
    
    play_frames = Play(step=frame_step)
    slide_frames = IntSlider()
    enter_frames = IntText()
            
    def update_save_to(change=None):
        global unlabeled_cap
        with save_to:
            clear_output(wait=True)
            if unlabeled_cap is not None:
                print(os.path.join(save_path.value, unlabeled_cap.name, "frame-{}.png".format(unlabeled_cap.current_index)))
            
    def update_image(plot, cap, frame_index=None):
        frame = cap.get_frame(frame_index)    
        update_save_to()
        with plot:
            clear_output(wait=True)
            plt.imshow(frame)
            plt.axis('off')
            plt.show()
            
    def load(b):        
        global labeled_cap
        global unlabeled_cap
        
        try: labeled_cap.release()
        except: pass
        
        try: unlabeled_cap.release()
        except: pass
        
        labeled_cap = VideoReader(labeled_video_path.value, frame_step)
        unlabeled_cap = VideoReader(unlabeled_video_path.value, frame_step)
    
        update_image(labeled_plot, labeled_cap)
        update_image(unlabeled_plot, unlabeled_cap)
        
        slide_frames.max = unlabeled_cap.frames
        enter_frames.max = unlabeled_cap.frames
        play_frames.max = unlabeled_cap.frames
        play_frames.interval = frame_step / unlabeled_cap.FPS * 1000
        
    @save_to.capture()
    def save(b):
        global unlabeled_cap
        if save_path.value and not os.path.exists(os.path.join(save_path.value, unlabeled_cap.name)):
            os.makedirs(os.path.join(save_path.value, unlabeled_cap.name))
        plt.imsave(os.path.join(save_path.value, unlabeled_cap.name, "frame-{}.png".format(unlabeled_cap.current_index)), unlabeled_cap.current_frame)
        
    def update_plot(change):
        global labeled_cap
        global unlabeled_cap
    
        update_image(labeled_plot, labeled_cap, change.new)
        update_image(unlabeled_plot, unlabeled_cap, change.new)
        
    labeled_plot.add_class('plot-fullsize')
    unlabeled_plot.add_class('plot-fullsize')
    
    labeled_video_path.observe(validate_path, names='value')
    unlabeled_video_path.observe(validate_path, names='value')
    save_path.observe(validate_path, names='value')
    enter_frames.observe(update_plot, names='value')
    save_path.observe(update_save_to, names='value')
    load_videos.on_click(load)
    save_button.on_click(save)
    
    widgets.jslink((play_frames, 'value'), (slide_frames, 'value'))
    widgets.jslink((enter_frames, 'value'), (slide_frames, 'value'))
    
    display(HTML('''
    <style>
        .invalid-path > input {
            color: red !important;
        }
        
        .plot-fullsize img {
            width: auto;
            height: calc(100% - 20px);
        }
        
        .plot-fullsize div:not(.jp-OutputArea-prompt) {
            width: auto;
            height: 100%;
        }
        
        .jp-RenderedImage {
            display: flex;
            justify-content: center;
            align-items: center;
        }
    </style>
    '''))
    
    display(VBox([
        HBox([
            VBox([
                Label('Labeled Video'),
                Label('Unlabeled Video')
            ]),
            VBox([
                labeled_video_path,
                unlabeled_video_path
            ], layout=flex_grow)
        ], layout=fluid),
        HBox([
            load_videos
        ], layout=Layout(justify_content='flex-end')),
        HBox([
            labeled_plot,
            unlabeled_plot
        ], layout=Layout(height='400px', width='100%', margin='40px 0 0 0')),
        HBox([
            play_frames,
            slide_frames,
            enter_frames
        ], layout=Layout(width='100%', justify_content='center', margin='10px 0 0 0')),
        HBox([
            Label('Save Root Folder'),
            save_path
        ], layout=Layout(margin='40px 0 0 0', width='100%')),
        HBox([
            Label('Saving to:'),
            save_to
        ]),
        HBox([
            Label(''), # In the future, actions/errors should be shown here
            save_button
        ], layout=Layout(flex='1 0 auto', justify_content='space-between'))
    ]), layout=fluid)