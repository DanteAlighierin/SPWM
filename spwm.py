from Xlib.display import Display
from Xlib import X, XK, Xatom
import commands
dpy = Display()
dpy.screen().root.grab_key(dpy.keysym_to_keycode(XK.string_to_keysym("F1")), X.Mod1Mask, 1,
        X.GrabModeAsync, X.GrabModeAsync)
dpy.screen().root.grab_button(1, X.Mod1Mask, 1, X.ButtonPressMask|X.ButtonReleaseMask|X.PointerMotionMask,
        X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE)
dpy.screen().root.grab_button(3, X.Mod1Mask, 1, X.ButtonPressMask|X.ButtonReleaseMask|X.PointerMotionMask,
X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE)
start = None
while 1:
    ev = dpy.next_event()
    if ev.type == X.KeyPress and ev.child != X.NONE:
        ev.child.configure(stack_mode=X.Above)
    elif ev.type == X.ButtonPress and ev.child != X.NONE:
        attr = ev.child.get_geometry()
        start = ev
    elif ev.type == X.MotionNotify and start:
        xdiff = ev.root_x - start.root_x
        ydiff = ev.root_y - start.root_y
        start.child.configure(
            x=attr.x + (start.detail == 1 and xdiff or 0),
            y=attr.y + (start.detail == 1 and ydiff or 0),
            width=max(1, attr.width + (start.detail == 3 and xdiff or 0)),
            height=max(1, attr.height + (start.detail == 3 and ydiff or 0)))
    elif ev.type == X.ButtonRelease:
        start = None
wm_name = 'spwm'
dpy = Display()
wids = []
root = dpy.screen().root
fw = dpy.screen().width_in_pixels // 2
fh = dpy.screen().height_in_pixels // 2
net_active_window = dpy.get_atom('_NET_ACTIVE_WINDOW')
net_client_list = dpy.get_atom('_NET_CLIENT_LIST')
net_supported = dpy.get_atom('_NET_SUPPORTED')
net_supporting_wm = dpy.get_atom('_NET_SUPPORTING_WM_CHECK')
net_wm_name = dpy.get_atom('_NET_WM_NAME')
args = sys.argv[1:] if len(sys.argv) == 6 else ['4', 'u', 'i', 'j', 'k']
mods = [X.Mod1Mask, X.Mod2Mask, X.Mod3Mask, X.Mod4Mask, X.Mod5Mask]
mod = mods[int(args[0]) - 1]
btn_mask = X.ButtonPressMask | X.ButtonReleaseMask | X.PointerMotionMask
root.grab_button(1, mod, 1, btn_mask, X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE)
root.grab_button(3, mod, 1, btn_mask, X.GrabModeAsync, X.GrabModeAsync, X.NONE, X.NONE)
root.change_attributes(event_mask = X.SubstructureNotifyMask)
root.change_property(net_supported, Xatom.ATOM, 32, [net_supported, net_active_window, net_client_list],)
support_window = root.create_window(0, 0, 10, 10, 0, dpy.screen().root_depth)
support_window.change_property(net_wm_name, Xatom.STRING, 8, wm_name,)

for window in [root, support_window]:
    window.change_property(net_supporting_wm, Xatom.WINDOW, 32, [support_window.id],)

def exit(i):
    sys.exit()

def kill_window(i):
    wids[-1].destroy()

def move(i):
    g = wids[-1].get_geometry()
    wids[-1].configure(x=(0 if i in [0, 2] else fw), y=(0 if i in [0, 1] else fh), width=g.width, height=g.height)

def resize(i):
    g = wids[-1].get_geometry()
    wids[-1].configure(x=g.x, y=g.y, width=(fw * (1 if i in [0, 2] else 2)), height=(fh * (1 if i in [0, 1] else 2)))

def is_win_at(w, i):
    g = w.get_geometry()
    return (g.x < fw if i in [0, 2] else g.x >= fw) and (g.y < fh if i in [0, 1] else g.y >= fh)

def switch(i):
    for w in (wids if is_win_at(wids[-1], i) else reversed(wids)):
        if is_win_at(w, i):
            activate_window(w)
            break

def activate_window(window):
    window.raise_window()
    window.set_input_focus(revert_to=X.RevertToNone, time=X.CurrentTime)
    try:
        wids.remove(window)
        wids.append(window)
    except ValueError:
        pass

bindings = {
    (mod, XK.XK_Escape): (kill_window, 0),
    (mod | X.ShiftMask, XK.XK_Escape): (exit, 0)
}
for i, k in enumerate(args[1:]):
    xk = XK.string_to_keysym(k)
    bindings[(mod, xk)] = (switch, i)
    bindings[(mod | X.ShiftMask, xk)] = (move, i)
    bindings[(mod | X.ControlMask, xk)] = (resize, i)

for key in bindings.keys():
    root.grab_key(dpy.keysym_to_keycode(key[1]), key[0], 1, X.GrabModeAsync, X.GrabModeAsync)

while 1:
    ev = dpy.next_event()
    if ev.type == X.MapNotify:
        try:
            attr = ev.window.get_attributes()
            if not attr.override_redirect and attr.map_state == X.IsViewable:
                wids.append(ev.window)
                activate_window(ev.window)
        except:
            pass
    elif ev.type == X.UnmapNotify:
        try:
            wids.remove(ev.window)
        except ValueError:
            pass
        if wids:
            activate_window(wids[-1])
        else:
            dpy.set_input_focus(root, X.RevertToPointerRoot, X.CurrentTime)
    elif ev.type == X.MapRequest:
        ev.window.map()
    elif ev.type == X.CirculateRequest:
        ev.window.circulate(ev.place)
    elif ev.type == X.ClientMessage and ev.client_type == net_active_window:
        activate_window(ev.window)
    elif ev.type == X.ButtonPress and ev.child != X.NONE:
        geom = ev.child.get_geometry()
        mouse_ev = ev
    elif ev.type == X.MotionNotify and mouse_ev:
        dx = ev.root_x - mouse_ev.root_x
        dy = ev.root_y - mouse_ev.root_y
        mouse_ev.child.configure(
            x=(geom.x + (dx if mouse_ev.detail == 1 else 0)),
            y=(geom.y + (dy if mouse_ev.detail == 1 else 0)),
            width=max(1, geom.width + (dx if mouse_ev.detail == 3 else 0)),
            height=max(1, geom.height + (dy if mouse_ev.detail == 3 else 0)))
    elif ev.type == X.ButtonRelease:
        mouse_ev = None
    elif ev.type == X.KeyPress and wids:
        handler = bindings.get((ev.state, dpy.keycode_to_keysym(ev.detail, 0)))
        if handler:
            handler[0](handler[1])

    root.change_property(net_client_list, Xatom.WINDOW, 32, [w.id for w in wids],)
root.change_property(net_active_window, Xatom.WINDOW, 32, [wids[-1].id] if wids else [X.NONE],)
