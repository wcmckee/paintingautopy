#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GIMP plug-in to backup open images at regular interval

# Starting from 'yahvuu' at http://
#   www.mail-archive.com/gimp-developer@lists.xcf.berkeley.edu/msg18118.html

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.


import os, time
import gtk,  shelve
import gettext, locale
#import pygtk
#pygtk.require('2.0')

from gobject import timeout_add_seconds
try:
    from gimpfu import *
except ImportError:
    import sys
    print("Note: GIMP is needed, '%s' is a plug-in.\n"%str(__file__))
    sys.exit(1)

# Internationalization 'i18n'
locale_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), \
                    'locale') # for users; administrator: gimp.locale_directory
gettext.install( "autosave_a", locale_directory, unicode=True )

class Save_recall():
    """
    Store, load and query dictionary name with string variable keyNr
    N.B.: this version does not accept unicode (eval?)
    """
    def __init__(self):
        folder = os.path.dirname(os.path.abspath(__file__))+os.sep+'autosave_a'
        self.file_shelf = folder+os.sep+'autosave.cfg'
        # if folder not there create it
        if not os.path.exists(folder): os.mkdir(folder)

    def save(self, keyNr):
        """
        keyNr is a string
        Store a keyNr dictionary in a shelf object
        """
        f = shelve.open(self.file_shelf)
        try: f[keyNr] = eval(keyNr)
        except: pass    #no dictionary with that name to save
        f.close()
        return

    def is_there(self, keyNr):
        """
        Return true if a dictionary keyNr exist
        """
        f = shelve.open(self.file_shelf)
        if f.has_key(keyNr): rep = True
        else: rep = False
        f.close()
        return rep

    def list_dict(self):
        """
        Return list of keys in shelf_file
        """
        rep = []
        f = shelve.open(self.file_shelf)
        rep = f.keys()
        rep.sort()
        f.close()
        return rep

    def recall(self, keyNr):
        """
        Retreive the dictionary keyNr, if there
        """
        f = shelve.open(self.file_shelf)
        dictio = None
        if self.is_there(keyNr):
            dictio = f[keyNr]
        else:
            print("No '%s' key exist in shelve file!"%keyNr)
        f.close()
        return dictio

locale.setlocale(locale.LC_ALL, '')
backupFiles = {}
active = False
cntr = 0
last_clock = 0

# conf. variables in a global dictionary & start with prev. stop_config
shelf = Save_recall()
if not shelf.is_there('default_config'):
    actual_dir = gtk.FileSelection()
    default_config = {
        'dir_BU'    : actual_dir.get_filename(),    # backup dir
        'source_ind': 2,                            # image(s) to save, index
        'exten_ind' : 0,                            # extension of file, index
        'kept'      : 1,                            # number of backup to keep
        'int_val'   : 600.0,                        # backup interval in second
        'start'     : False                         # at start of interval, bool.
    }
    shelf.save('default_config')
config = {}
if shelf.is_there('laststop_config'): config_act = 'laststop_config'
else: config_act = 'default_config'
config = shelf.recall(config_act)
# Preset mode messages
msga = _("Adding numbered preset: a consecutive sequence of 5 .")
msgr = _("Replacing numbered preset: select number by 'Recall...'.")

for i in range(5): exec('recall_config%d'%i + ' = {}')

class Control_Autosave(gtk.Window):
    """
    GUI for interaction with autosave_a and calling repeatedly
    the timing fonction
    """
    def __init__(self, img, parent=None):
        global config, exten
        self.image = img.name
        self.recycle = False

        #print("Begin autosave_a with launching image: "+str(image))
        # Create the window
        win = gtk.Window.__init__(self)
        #self.connect('destroy', lambda *w: gtk.main_quit())
        self.connect('destroy', self.on_destroy)
        self.set_title(_("Autosave_a Panel"))

        # next block is for the window icon --------------------------------
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), \
                                'autosave_a')
        try:
            self.set_icon_from_file( icon_dir+os.sep+'autosave-icon.png')
        except:
            print("Autosave warning: did not find the icon file!")
        # ------------------------------------------------------------------

        self.set_focus_on_map(True)
        self.set_border_width(8)

        sup_vbox = gtk.VBox(False, 8)
        self.add(sup_vbox)
        label = gtk.Label(_(" Choose your parameters below and press 'Start';")\
                         +_("\nonly button active after 'Start' is 'Stop'. Then")\
                         +_("\nminimize (close=stop) the window until needed."))
        # pack_start(child, expand=True, fill=True, padding=0)
        sup_vbox.pack_start(label, False, False, 0)

        ##############################
        ## Directory ->
        dir_frame = gtk.Frame(_("Directory"))
        sup_vbox.pack_start(dir_frame, padding=5)
        hbox = gtk.HBox(False, 4)
        dir_frame.add(hbox)

        # button to choose dir (to launch gtk.FileSelection)
        button = gtk.Button(_("Change the"))
        button.connect('clicked', self.on_choose_dir_clicked)
        hbox.pack_start(button, False, False, 0)
        # put the actual dir beside it
        label = gtk.Label(_("backup dir.: "))
        hbox.pack_start(label, False, False, 0)

        self.label = gtk.Label('')
        self.label.set_has_tooltip(True)
        self.label.set_tooltip_text(_("The actual folder where the backup")\
                                    +_("\nwill be"))
        hbox.pack_start(self.label, False, False, 0)

        ##############################
        ## Files ->
        file_frame = gtk.Frame(_("Files"))
        sup_vbox.pack_start(file_frame, padding=5)
        table = gtk.Table(2, 3)
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        file_frame.add(table)

        # column headers
        label = gtk.Label(_("image"))
        label.set_has_tooltip(True)
        label.set_tooltip_text(_("The source(s) of the backup file from:")\
                                    +_("\nthe one to all"))
        table.attach(label, 0, 1, 0, 1)
        label = gtk.Label(_("extension"))
        label.set_tooltip_text(_("To control the compression of 'xcf' file from:")\
                                    +_("\nmore to less"))
        table.attach(label, 1, 2, 0, 1)
        label = gtk.Label(_("nr kept"))
        label.set_has_tooltip(True)
        label.set_tooltip_text(_("Number of backup kept for the same ")\
                                    +_("\nsession and image ID"))
        table.attach(label, 2, 3, 0, 1)

        # autosave image source + extension: xcfbz2 or xcfgz
        self.source = [_("Launching one"), _("All changed"), \
                      _("All open")]
        self.combo1 = gtk.combo_box_new_text()
        [self.combo1.append_text(x) for x in self.source]
        self.combo1.connect("changed",  self.on_all_changed)
        table.attach(self.combo1, 0, 1, 1, 2)

        exten = [".xcf.bz2", ".xcf.gz", ".xcf", ".png", ".jpg"]
        self.combo = gtk.combo_box_new_text()
        [self.combo.append_text(x) for x in exten]
        self.combo.connect("changed",  self.on_file_ext_change)
        table.attach(self.combo, 1, 2, 1, 2)

        # number of backup to keep of current image: 1 -> 9
        self.interv = gtk.SpinButton(adjustment=None, climb_rate=1.0, digits=0)
        self.interv.set_range(1, 9)
        self.interv.set_increments(1, 1)
        self.interv.set_numeric(True)
        self.interv.connect('value-changed',  self.on_nr_kept_change)
        table.attach(self.interv, 2, 3, 1, 2)

        ##############################
        ## Time ->
        time_frame = gtk.Frame(_("Time"))
        sup_vbox.pack_start(time_frame, padding=5)
        hbox = gtk.HBox(False, 4)
        time_frame.add(hbox)

        self.rbtn = gtk.CheckButton(_("At start? "))        
        self.rbtn.connect("toggled", self.on_toggled_check, None)
        self.rbtn.set_has_tooltip(True)
        self.rbtn.set_tooltip_text(_("If check: begins at the interval start,")\
                                  +_("\nif not at the end."))
        hbox.pack_start(self.rbtn, False, False, 0)

        # put the header for time interval beside it
        label = gtk.Label(_("Backup interval (min):"))
        hbox.pack_start(label, False, False, 0)
        # gtk.SpinButton(adjustment=None, climb_rate=0.0, digits=0)
        self.interv1 = gtk.SpinButton(adjustment=None, climb_rate=0.0, digits=1)
        self.interv1.set_range(1, 999)
        self.interv1.set_increments(0.1, 5)
        self.interv1.set_numeric(True)
        self.interv1.connect('value-changed',  self.on_time_interval_change)
        hbox.pack_start(self.interv1, False, False, 0)

        ##############################
        ## Controls ->
        hbox = gtk.HBox(False, 8)
        sup_vbox.pack_start(hbox, False, False, 0)
        # button to save current parameters now
        self.choices = shelf.list_dict()
        self.nr = 0     # number of save_config
        for i in range(len(self.choices)):
            if self.choices[i][:5] == 'recal': self.nr += 1
        if self.nr == 5 : self.recycle = True
        self.button = gtk.Button(_("Save config ")+str(self.nr%5))
        self.button.set_has_tooltip(True)
        self.button.set_tooltip_text(_("Will save all the above parameters on disk")\
                            +_("\nfor later usage with button 'Recall config'"))
        self.button.connect('clicked', self.on_save_now_clicked)
        hbox.pack_start(self.button, False, False, 0)

        # place a remenber param. combobox
        hbox2 = gtk.HBox()
        #hbox2.set_border_width(10)
        hbox.pack_start(hbox2)
        self.combo_box = gtk.combo_box_new_text()
        self.combo_box.set_wrap_width(1)
        # new 'choices' list to unable lang. translation
        self.choices_combo = [_("Default config")]
        conf_act = 0
        for i in range(len(self.choices)):
            if i > 0 :
                if self.choices[i][:5] == 'lasts':
                    self.choices_combo.append(_("LastStop config"))
                    conf_act = i
                else:
                    self.choices_combo.append(_("Recall config ")+\
                        self.choices[i][-1:])
            self.combo_box.append_text(self.choices_combo[i])
        self.combo_box.set_active(conf_act)
        self.combo_box.set_has_tooltip(True)
        self.combo_box.set_tooltip_text(_("Choose from existing config presets"))
        hbox2.pack_start(self.combo_box)
        self.combo_box.connect("changed", self.choice_i_cb)

        # icon to indicate state
        self.stock_ic = gtk.Image()
        self.stock_ic.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.stock_ic.set_has_tooltip(True)
        self.stock_ic.set_tooltip_text(_("Indicates if the widgets to the left")\
                +_("\nand above are frozen or not"))
        hbox.pack_start(self.stock_ic, False, False, 0)
        hbox.pack_start(gtk.VSeparator(), expand=False)

        # place a start-stop button
        self.button1 = gtk.Button(_("Start"))
        self.button1.connect('pressed', self.on_activate_clicked)
        hbox.pack_start(self.button1, True, True, 3)

        ##############################
        ## Info during ->
        info_frame = gtk.Frame(_("Info"))
        sup_vbox.pack_start(info_frame, padding=5)
        vbox = gtk.VBox(False, 0)
        info_frame.add(vbox)

        if self.recycle:
            msgi = msgr
        else:
            msgi = msga
        self.label1 = gtk.Label(msgi)
        self.label1.set_alignment(0.1, 0.2)
        vbox.pack_start(self.label1, False, False, 0)

        self.show_all()
        self.set_config()
        timeout_add_seconds(1, self.timer_action)

    def on_destroy(self, win):
        end = time.strftime("%a, %d %b %Y %H:%M:%S")
        if active:
            end_message = _("INFO:\n  was closed on:\n %s;")%end
            if cntr > 1 : end_message += _("\nafter %d rounds of backup.")%cntr
            else : end_message += _("\nafter %d round of backup.")%cntr
            gimp.message(end_message)
        self.destroy()
        gtk.main_quit()

    def set_config(self):
        if not active:
            self.label.set_text(config['dir_BU'])
            self.combo1.set_active(config['source_ind'])
            self.combo.set_active(config['exten_ind'])
            self.interv.set_value(config['kept'])
            self.interv1.set_value(config['int_val']/60.0)
            if self.rbtn.get_active() != config['start']:
                self.rbtn.set_active(config['start'])
            return

    def on_choose_dir_clicked(self, button):
        global config
        if not active:
            direc = gtk.FileSelection(_('Autosave_a to Directory'))
            direc.run()
            config['dir_BU'] = direc.get_filename()
            self.label.set_text(config['dir_BU'])
            direc.destroy()

    def on_nr_kept_change(self, spinbutton):
        global config
        if not active:
            config['kept'] = spinbutton.get_value_as_int()
        else: spinbutton.set_value(config['kept'])

    def on_toggled_check(self, rbtn, data=None):
        global config
        if not active :
            if self.rbtn.get_active() != config['start']:
                config['start'] = not config['start']
            else: self.rbtn.set_active(config['start'])

    def on_time_interval_change(self, spinbutton):
        global config
        if not active:
            config['int_val'] = spinbutton.get_value() * 60.0
        else: spinbutton.set_value(config['int_val']/60.0)

    def on_all_changed(self, combo1):
        global config
        if not active:
            config['source_ind'] = combo1.get_active()
        else: combo1.set_active(config['source_ind'])

    def on_file_ext_change(self, combo):
        global config
        if not active:
            config['exten_ind'] = combo.get_active()
        else: combo.set_active(config['exten_ind'])

    def on_save_now_clicked(self, button):
        if not active:
            # two mode: 1) self.recycle = False, 2) self.recycle = True
            #   in mode 2) self.nr is given by 'choice_i_cb()' for replacement

            global recall_config0, recall_config1, recall_config2, recall_config3,\
                recall_config4
            if self.nr == 0: recall_config0 = config
            elif self.nr == 1: recall_config1 = config
            elif self.nr == 2: recall_config2 = config
            elif self.nr == 3: recall_config3 = config
            elif self.nr == 4: recall_config4 = config

            re_txt = 'recall_config%d'%self.nr
            shelf.save(re_txt)
            #print("Dictionary in save_now: "+str(shelf.recall(re_txt)))
            if not self.recycle:
                trans_txt = _("Recall config ")+str(self.nr)
                self.choices = shelf.list_dict()
                self.combo_box.append_text(trans_txt)
                self.choices_combo.append(trans_txt)
                self.combo_box.set_active(self.choices_combo.index(trans_txt))
                self.nr += 1
                if self.nr > 4 :
                    self.nr = 0
                    self.recycle = True
                    self.label1.set_text(msgr)
            save_dict = _('Save config ')+str(self.nr%5)
            button.set_label(save_dict)

    def choice_i_cb(self, combo_box):
        global config
        if not active:
            j = self.combo_box.get_active()
            config = shelf.recall(self.choices[j])
            self.set_config()
            if self.recycle and self.choices[j][:5] == 'recal':
                self.nr = int(self.choices[j][-1:])
                self.button.set_label(_('Save config %d>')%self.nr)

    def on_activate_clicked(self, switch, data=None):
        global active, config, laststop_config, last_clock   #stop_config,

        if switch.get_label() == _("Start"):
            active = True
            switch.set_label(_("Stop"))
            self.stock_ic.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            # a message to remenber the saving dir
            self.last_clock = time.mktime(time.localtime())
            begin = time.strftime("%a, %d %b %Y %H:%M:%S")
            gimp.message(_("INFO:\n  was started on:\n")\
                +_(" %s;\nthe backup directory is\n %s")%(begin, config['dir_BU']))
        else:
            active = False
            end = time.strftime("%a, %d %b %Y %H:%M:%S")
            end_message = _("INFO:\n  was stopped on:\n %s;")%end
            if cntr > 1 : end_message += _("\nafter %d rounds of backup.")%cntr
            else : end_message += _("\nafter %d round of backup.")%cntr
            # save the stop config
            laststop_config = config
            shelf.save('laststop_config')
            gimp.message(end_message)
            self.button1.connect("released", gtk.main_quit)
        return

    def timer_action(self):
        if active:
            clock_cur = time.mktime(time.localtime()) - self.last_clock
            at_start = cntr == 0 and config['start']
            at_end = clock_cur > config['int_val']
            if at_start or at_end:
                self.backup_time()
                if at_end: self.last_clock += config['int_val']
            else:
                msgb = _("Backup round done: %d;  next in %d s .")\
                        %(cntr, config['int_val']-clock_cur)
                self.label1.set_text(msgb)
                self.show_all()
            
        return True

    def backup_time(self):
        """
        A modification of 'autosave.py'
        """
        global backupFiles, cntr

        cntr += 1
        self.label1.set_text(_("Saving round #%d now...")%cntr)
        self.show_all()

        img_list = gimp.image_list()
        curImages = {}
        # to find unsave change: dirty = k.dirty, is True or False
        for k in img_list :
            key = k.ID
            if config['source_ind'] == 2 : curImages[key] = k
            elif  k.dirty and config['source_ind'] == 1 : curImages[key] = k
            elif k.name == self.image and config['source_ind'] == 0 :
                curImages[key] = k

        # if backup only the changed image, the nr kept can be surprising
        curIDs = curImages.keys()
        oldIDs = backupFiles.keys()
        newIDs = [x for x in curIDs if x not in oldIDs];
        delIDs = [x for x in oldIDs if x not in curIDs];

        # remove closed images in backups list
        for id in delIDs:
            #print("The backup file '%s', removed from the list."%backupFiles[id])
            del(backupFiles[id])

        if curIDs == []:
            # no image to backup
            print("No image to backup in cycle %d"%cntr)
            return

        # backupFiles is a list of filename stub and cycle counter for keeping
        for id in newIDs:
            cur_name = curImages[id].name[:curImages[id].name.find('.')]
            prefix = 'BU-ID' + str(id) + '-' + cur_name + '-'
            backupFiles[id] = [config['dir_BU'] + os.sep + prefix, cntr]
            #print("Backup file '%s', added to the list."%backupFiles[id])

        # backup images by replacing the last file if >= kept;
        for id, stub in backupFiles.iteritems():
            if cntr- stub[1] >= config['kept']:
               os.remove(stub[0]+str(stub[1])+exten[config['exten_ind']])
               backupFiles[id][1] += 1
            img = curImages[id]
            filename = stub[0] + str(cntr) + exten[config['exten_ind']]
            try:
                pdb.gimp_file_save(img, img.active_drawable, filename, filename)
            except:
                print("ERROR in backup image: "+filename)

        return


################################################################################

def autosave_a(image, item):

    co_au = Control_Autosave(image)
    gtk.main()
    pdb.gimp_displays_flush()
    #print("List of dict. in shelf: "+str(shelf.list_dict()))

register(
        "autosave_a",
        _("It configures auto-backup images, starts and stops it.")\
            +_("\nFrom: ")+str(__file__),
        "Periodically saves chosen opened images to a backup directory",
        "R. Brizard",
        "(c) R. Brizard",
        "2012",
        _("Auto save..."),
        "*",
        [(PF_IMAGE, "img", "IMAGE:", None),
         (PF_DRAWABLE, "drawable", "DRAWABLE:", None)],
        [],
        autosave_a,
        menu = "<Image>/"+_("Plugins-Python/File"))

main()
