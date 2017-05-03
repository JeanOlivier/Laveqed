#!/usr/bin/python
# -*- coding: utf-8 -*-
from Tkinter import *
from ttk import *
from ScrolledText import ScrolledText as Text
from PIL import Image, ImageTk
import tkFileDialog,os,cairo,tempfile,time,shutil,tkFont
from laveqed import laveqed
from rsvg_windows import rsvg_windows
try:
    import rsvg
except ImportError:
    rsvg=rsvg_windows()	# Untested


TITLE = 'laveqed GUI'
APP_WIN_WIDTH = 800
APP_WIN_HEIGHT = 400
FONTNAME='Ubuntu Mono'
LOGOFILENAME='laveqed_logo.svg'
CONFIGFILE='laveqed_config.xml'

class laveqed_gui(object):

    def __init__(self, title):
        print('Starting \t\t:\tWelcome in laveqed\'s GUI!')
        os.environ['XMODIFIERS'] = "@im=none" # Fix for non-working ^ after a while
        self.win=Tk()
        self.win.title(title)
        self.center(self.win)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.previewSize=(713,45)
        self._topLevelOpened = False
        self.displayScale = 1

        self.buildGUI()
        self._set_vars() # Sets variables for use by laveqed, also creates temp folder and cd into it
        self._makelogo() # Either loads pre-calculated logo or generates it.

        self.text_widget.focus() # So we can type right away!


    def _buildFrames(self):
        self.main_frame=Frame(self.win)
        self.main_frame.pack(fill='both',expand=True)
        
        # So the picture isn't too much to the top
        self.space_frame=Label(self.main_frame)
        self.space_frame.pack(side='top',fill='both', expand=False, padx=4, pady=10)
        
        self.top_frame=LabelFrame(self.main_frame,relief=FLAT)
        self.top_frame.pack(side='top',fill='both', expand=True, padx=4, pady=4)
        
        self.png_frame=Label(self.top_frame,anchor='center')
        self.png_frame.pack(fill='both', expand=True, padx=4, pady=4)

        self.bottom_frame=LabelFrame(self.main_frame,relief=FLAT)
        self.bottom_frame.pack(side='bottom', fill=X, expand=False, padx=4, pady=4)
        
        self.text_frame=LabelFrame(self.bottom_frame,relief=FLAT)
        self.text_frame.pack(side='left', fill=X, expand=True, padx=4, pady=4)

    def _tag_configure(self, text):
        # Color tags for syntax highlight
        text.tag_configure('red',foreground='red')
        text.tag_configure('green',foreground='green')
        text.tag_configure('purple',foreground='purple')
        text.tag_configure('blue',foreground='blue')
        # Bold baby!
        text.tag_configure('bold',font=self.bold_font)


    def _buildWidgets(self):
        self.text_widget=Text(self.text_frame,bd=2,padx=4,pady=4,\
                wrap=WORD,font=(FONTNAME,14),undo=True)
        self.text_widget.pack(fill='both',expand=True,padx=4,pady=4)
        self.bold_font = tkFont.Font(self.text_widget, self.text_widget.cget("font"))
        self.bold_font.configure(weight="bold")
        self._tag_configure(self.text_widget)

#        self.text_widget=Text(self.text_frame,bd=2,padx=4,pady=4,\
#                wrap=WORD,font=(FONTNAME,14),undo=True)
#        self.text_widget.pack(fill='both',expand=True,padx=4,pady=4)
#        # Color tags for syntax highlight
#        self.text_widget.tag_configure('red',foreground='red')
#        self.text_widget.tag_configure('green',foreground='green')
#        self.text_widget.tag_configure('purple',foreground='purple')
#        self.text_widget.tag_configure('blue',foreground='blue')
#        # Bold baby!
#        #self.orig_font = tkFont.Font(self.text_widget, self.text_widget.cget("font"))
#        self.bold_font = tkFont.Font(self.text_widget, self.text_widget.cget("font"))
#        self.bold_font.configure(weight="bold")
#        self.text_widget.tag_configure('bold',font=self.bold_font)
#        #self.text_widget.tag_configure('plain',font=self.orig_font,foreground='black',background='white')





    def _buildMenus(self):
        self.menubar=Menu(self.win)
        # File menu
        filemenu=Menu(self.menubar,tearoff=0)
        filemenu.add_command(label="Open", command=self.open_svg,accelerator='Ctrl+O')
        filemenu.add_command(label="Save as...", command=self.save_svg,accelerator='Ctrl+S')
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.close,accelerator='Ctrl+Q')
        self.menubar.add_cascade(label="File", menu=filemenu)
        # laveqed menu
        laveqedmenu=Menu(self.menubar,tearoff=0)
        laveqedmenu.add_command(label='Run',command=self.build_svg,accelerator='Ctrl-Enter')
        laveqedmenu.add_command(label='Preferences',command=self.preferences,accelerator='Ctrl-P')
        self.menubar.add_cascade(label="laveqed", menu=laveqedmenu)
        
        self.win.config(menu=self.menubar)


    def _set_vars(self):
        if os.path.isfile(CONFIGFILE):
            pass    # Parse the xml and set vars accordingly
        else:       # No config file? -> Get defaults laveqed -ambles and scale
            tmp=laveqed()   
            self.preamble=tmp.preamble
            self.postamble=tmp.postamble
            self.scale=tmp.scale
            self.eqonly=False   # Loads -ambles by default if eqonly == False
        # Creating a temporary folder to work inside of
        self.owd=os.getcwd()    # Original Working Directory, for friendly fileOpenDialog
        self.cwd=tempfile.mkdtemp()
        print('Making temp folder\t:\t'+self.cwd)
        os.chdir(self.cwd)

        try :
            shutil.copy2(self.owd+'/'+LOGOFILENAME,self.cwd+'/'+LOGOFILENAME)
        except:
            pass
         

    def _binding(self):
        # Allows select all in Text Widget
        self.win.bind_class("Text","<Control-a>", self.selectall)
        # Main window binds
        self.win.bind('<Control-Return>',self.build_svg_fixCtrlReturn)
        self.win.bind('<Control-s>',self.save_svg)
        self.win.bind('<Control-o>',self.open_svg_fixCtrlO)
        self.win.bind('<Control-p>', self.preferences)
        self.win.bind('<Control-q>',self.close)
        # Text widget binds
        self.text_widget.bind('<Control-h>',self.hat)
        self.text_widget.bind('<KeyRelease>',self.set_syntax)
        # SVG binds
        self.win.bind('<Control-plus>', self.ZoomInSVG)
        self.win.bind('<Control-minus>', self.ZoomOutSVG)
        self.win.bind('<Control-0>', self.ZoomResetSVG)


    def _makelogo(self):
        self.name=LOGOFILENAME[:-4]
        if not os.path.isfile(LOGOFILENAME):
            equation=r'\text{L\hspace{-3.5pt}\raisebox{2pt}{\scriptsize A}\!}{\color{gray!68}\text{\TeX}}\text{ V{\color{gray!80}ectorial} Eq{\color{gray!80}uation} Ed{\color{gray!80}itor}}'
            self.text_widget.insert('1.0',equation)
            self.build_svg()
            self.text_widget.delete('1.0',END)
        self.load_svg()



    def buildGUI(self):
        # Style
        #self.win.style=Style()
        #self.win.style.theme_use('clam')
        #Order matters for some elements; e.g. better build frames before widgets
        self._buildFrames()
        self._buildWidgets()
        self._buildMenus()
        self._binding()


    def center(self, win, x=APP_WIN_WIDTH, y=APP_WIN_HEIGHT):
        win.update_idletasks()
        width = x
        height = y
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))


    def load_svg(self,event=None):
        filename=self.name+'.svg'
        if os.path.isfile(filename):
            #self.tk_image=self.svgPhotoImage(filename, scale=self.displayScale)
            self.openDisplaySVG(filename)

            print('Loading svg file\t:\t'+filename+' (Success!)')
        # If opening failed, put a blank image the same size as SVGLOGOFILE
        else:   # Note, this should never occurs now... Left here because
            print('Loading svg file\t:\t'+filename+' (Failed!)')
            self.tk_image = ImageTk.PhotoImage('RGBA')
            self.image=Image.new('RGB',self.previewSize,self.win['background'])
            self.tk_image.paste(self.image)
        self.png_frame.config(image=self.tk_image)

        
    def close(self,var=None):
        print('Removing temp folder\t:\t'+self.cwd)
        shutil.rmtree(self.cwd) # Removing the temporary folder we worked in
        print("Exiting\t\t\t:\tCiao!")
        self.win.destroy()


    def selectall(self, event):
        event.widget.tag_add("sel","1.0","end")

    def hat(self,event):
        event.widget.insert(INSERT,'^^')

    def fixCtrlReturn(self,event=None):
        self.text_widget.delete('%s-1c'%INSERT, INSERT)

    def fixCtrlO(self,event=None):
        self.text_widget.delete(INSERT, '%s+1c'%INSERT)

    def run(self):
        self.win.mainloop()



    def build_preferences(self, pref, event=None):
        pre_label = Label(pref, text='Preamble:')
        post_label = Label(pref, text='Postamble:')
        pre_text = Text(pref, bd=2,padx=4, pady=4, wrap=WORD,\
                font=(FONTNAME,12), undo=True)
        post_text = Text(pref, bd=2,padx=4, pady=4, wrap=WORD,\
                font=(FONTNAME,12), undo=True)
        scale_label = Label(pref, text='Scale:')
        scale_entry = Entry(pref, width = 2)
        save_button = Button(pref, text='OK')
        
        padval=10
        pre_label.grid(row=0, column=0, sticky='w', padx=padval,\
                pady=(padval,0))
        pre_text.grid(row=2, column=0, sticky='nwse', padx=padval,\
                pady=(0,padval))
        post_label.grid(row=3, column=0, sticky='w', padx=padval,\
                pady=(padval,0))
        post_text.grid(row=4, column=0, sticky='nwse', padx=padval,\
                pady=(0,padval))
        scale_label.grid(row=5, column=0, sticky='w', padx=padval,\
                pady=(0,padval))
        scale_entry.grid(row=5, column=0, sticky='w', padx=50,\
                pady=(0,padval))
        save_button.grid(row=5, column=0, sticky='e', padx=padval,\
                pady=(0,padval))

        pref.columnconfigure(0, weight=1)
        pref.rowconfigure(2, weight=4)
        pref.rowconfigure(4, weight=5)

        pre_text.insert('1.0', self.preamble)
        post_text.insert('1.0', self.postamble)
        scale_entry.insert(0, self.scale)

        self._tag_configure(pre_text)
        self._tag_configure(post_text)

        def set_syntax_pref(event=None):
            self._set_syntax(pre_text)
            self._set_syntax(post_text)
        
        pre_text.bind('<KeyRelease>', set_syntax_pref)
        post_text.bind('<KeyRelease>', set_syntax_pref)
        set_syntax_pref()
        pre_text.focus()

        def save_pref(event=None):
            self.preamble = os.linesep.join([s for s \
                    in pre_text.get('1.0', END).splitlines() if s.strip()])
            self.postamble = os.linesep.join([s for s \
                    in post_text.get('1.0', END).splitlines() if s.strip()])
            self.scale = scale_entry.get()
            print('Editing Preferences\t:\tSaving Preferences')
            pref._destroy()

        save_button.bind('<ButtonRelease-1>', save_pref)
        save_button.bind('<Return>', save_pref)
        pref.bind('<Control-s>', save_pref)
        pref.bind('<Control-q>', pref._destroy)
        

    def preferences(self,event=None):
        if self._topLevelOpened:
            return
        else:
            print('Editing Preferences\t:\tOpening Dialog')
            self._topLevelOpened = True

        def _destroy(self_, event=None):
            print('Editing Preferences\t:\tClosing Dialog')
            self_.destroy()
            self._topLevelOpened = False

        Toplevel._destroy = _destroy

        # Create the window
        pref = Toplevel(self.win)
        pref.title('Preferences')
        self.center(pref, x=APP_WIN_WIDTH/2, y=APP_WIN_HEIGHT)
        
        # Create the Widgets
        self.build_preferences(pref, event)
        
        # Closes with a message
        pref.protocol("WM_DELETE_WINDOW", pref._destroy)

        # Pref dialog always on top and to focus
        pref.grab_set()
        pref.wm_attributes("-topmost", 1)


    def build_svg_fixCtrlReturn(self,event=None):
        # Fixes accidental <Return> catched by text_widget when <C-Return> is pressed
        self.fixCtrlReturn() 
        self.build_svg()
    def build_svg(self,event=None):
        self.name=time.strftime('%Y-%m-%d_%H-%M-%S')  # Temp filename is time in seconds since epoch. 
            # Strips first char in case it's a '-' which latex understands as an argument 
        print('Building svg\t\t:\t'+self.name+'.svg')
        equation=os.linesep.join([s for s \
                in self.text_widget.get('1.0',END).splitlines() if s.strip()])
            # Removes empty lines so latex doesn't freak out
        tmp=laveqed(equation,name=self.name,scale=self.scale,cleanAfter=False,eqonly=self.eqonly)
        tmp.preamble=self.preamble
        tmp.postamble=self.postamble
        print('\n\t======= LaTeX output begins =======')
        try:
            tmp.makesvg()
            print('\t=======  LaTeX output ends  =======\n')
            self.load_svg()
        except:
            print('\t======= LaTeX output ends =======\n')
            print('Error building svg file\t:\tCheck LaTeX Syntax')


    def save_svg(self,event=None):
        print('Saving svg\t\t:\tOpening Dialog')
        filename=tkFileDialog.asksaveasfilename(filetypes=[('laveqed SVG file','.svg')],\
                initialdir=self.owd,defaultextension='.svg',initialfile=self.name+'.svg')
        try:
            shutil.copy2(self.name+'.svg',filename)
            print('Saving svg\t\t:\tFile saved as '+filename)
        except:
            print('Saving svg\t\t:\tOperation cancelled')
        
    def open_svg_fixCtrlO(self,event=None):
        # Fixes accidental linebreak at INSERT+1 catched by text_widget when <C-o> is pressed
        self.fixCtrlO()
        self.open_svg()
    def open_svg(self,event=None):
        print('Opening svg\t\t:\tOpening Dialog')
        self.name=tkFileDialog.askopenfilename(filetypes=[('laveqed SVG file','.svg')],\
                initialdir=self.owd,defaultextension='.svg').replace('.svg','')
        if not self.name:
            print('Opening svg\t\t:\tOperation cancelled')
        else:
            print('Opening svg\t\t:\t'+self.name+'.svg')
            tmp=laveqed(eqonly=self.eqonly)
            tmp.loadsvg(self.name)
            if self.eqonly:
                print('Loading laveqed equation\t:\tequation')
                self.equation=tmp.equation
            else:
                print('Loading laveqed vars\t:\t-ambles, equation and scale')
                self.preamble,equation,self.postamble,self.scale\
                        =tmp.preamble,tmp.equation,tmp.postamble,tmp.scale
            self.load_svg()
            self.text_widget.delete('1.0',END)
            self.text_widget.insert('1.0',equation)
            self.set_syntax()


    def highlight_pattern(self, event, pattern, tag, start="1.0", end="end", regexp=False):
        # Adapted from http://bit.ly/UMdj9q
        '''Apply the given tag to all text that matches the given pattern
        If 'regexp' is set to True, pattern will be treated as a regular expression
        '''

        start = event.index(start)
        end = event.index(end)
        event.mark_set("matchStart",start)
        event.mark_set("matchEnd",start)
        event.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = event.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            event.mark_set("matchStart", index)
            event.mark_set("matchEnd", "%s+%sc" % (index,count.get()))
            event.tag_add(tag, "matchStart","matchEnd")

    def _set_syntax(self, text):
        # \\ ^ & and numbers including reals and size in "pt" -> red
        # {}[] -> purple
        # \alpha or (\!\#\&\$\,\;\:) -> green
        # % until EOL is comment (blue)
        # Alignment '&' is bold

        # First clearing all tags. e.g. avoids '{}<left>A' to color '{A}' all in purple
        for i in ['red','purple','green','blue','bold']:
            text.tag_remove(i,'1.0','end')
        # Parsing the text and setting tags
        self.highlight_pattern(text,r'\\\\|\^|([-\.]?|^)[0-9]\.?(pt| pt)?|\\%','red',regexp=True)       
        self.highlight_pattern(text,r'[\[\]\{\}\(\)]', 'purple',regexp=True)           
        self.highlight_pattern(text,r'\\([a-zA-Z]+|[!#&\$,;:])', 'green',regexp=True)
        self.highlight_pattern(text,r'([^\\]|^)%.*','blue',regexp=True)
        self.highlight_pattern(text,r'&','bold',regexp=True)

    def set_syntax(self, event=None):
        self._set_syntax(self.text_widget)


#        # \\ ^ & and numbers including reals and size in "pt" -> red
#        # {}[] -> purple
#        # \alpha or (\!\#\&\$\,\;\:) -> green
#        # % until EOL is comment (blue)
#        # Alignment '&' is bold
#        text=self.text_widget
#        # First clearing all tags. e.g. avoids '{}<left>A' to color '{A}' all in purple
#        for i in ['red','purple','green','blue','bold']:
#            text.tag_remove(i,'1.0','end')
#        # Parsing the text and setting tags
#        self.highlight_pattern(text,r'\\\\|\^|([-\.]?|^)[0-9]\.?(pt| pt)?|\\%','red',regexp=True)       
#        self.highlight_pattern(text,r'[\[\]\{\}\(\)]', 'purple',regexp=True)           
#        self.highlight_pattern(text,r'\\([a-zA-Z]+|[!#&\$,;:])', 'green',regexp=True)
#        self.highlight_pattern(text,r'([^\\]|^)%.*','blue',regexp=True)
#        self.highlight_pattern(text,r'&','bold',regexp=True)
        

        
    def svgPhotoImage(self,file_path_name, scale=1): # TODO Fix (if can be) AA artefacts at sharp alpha edges
        "Returns a ImageTk.PhotoImage object represeting the svg file" 
        # Based on pygame.org/wiki/CairoPygame and http://bit.ly/1hnpYZY        
        svg = rsvg.Handle(file=file_path_name)
        width, height = svg.get_dimension_data()[:2]
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width*scale), int(height*scale))
        context = cairo.Context(surface)
        context.scale(scale,scale)
        #context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        svg.render_cairo(context)
        tk_image=ImageTk.PhotoImage('RGBA')
        image=Image.frombuffer('RGBA',(int(width*scale),int(height*scale)),surface.get_data(),'raw','BGRA',0,1)
        tk_image.paste(image)
        return(tk_image)



    def openSVG(self, file_path_name):
        svg = rsvg.Handle(file=file_path_name)
        width, height = svg.get_dimension_data()[:2]
        self.openedSVG = dict(svg=svg, width=width, height=height)


    def updateOpenedSVG(self):
        svg = self.openedSVG['svg']
        width = self.openedSVG['width']
        height = self.openedSVG['height']

        scale = self.displayScale

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width*scale), int(height*scale))
        context = cairo.Context(surface)
        context.scale(scale,scale)
        context.set_antialias(cairo.ANTIALIAS_DEFAULT)
        svg.render_cairo(context)
        tk_image=ImageTk.PhotoImage('RGBA')
        image=Image.frombuffer('RGBA',(int(width*scale),int(height*scale)),surface.get_data(),'raw','BGRA',0,1)
        tk_image.paste(image)

        self.tk_image = tk_image
        self.tk_image.paste(image)
        self.png_frame.config(image=self.tk_image)

    
    def openDisplaySVG(self, file_path_name):
        self.openSVG(file_path_name)
        self.updateOpenedSVG()


    def ZoomInSVG(self, event=None):
        # Avoids slugginess caused by zooming too much by accident
        if self.displayScale < 5:
            self.displayScale *= 1.05
            self.updateOpenedSVG()

    def ZoomOutSVG(self, event=None):
        # Avoid problems with too small image
        self.displayScale /= 1.05
        if self.displayScale < 0.05:
            self.displayScale = 0.05
        self.updateOpenedSVG()

    def ZoomResetSVG(self, event=None):
        self.displayScale = 1
        self.updateOpenedSVG()


if __name__ == '__main__':
    tmp=laveqed_gui(TITLE).run()


