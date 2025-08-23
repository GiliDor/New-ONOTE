# ONOTE Page-Based Desktop Architecture Guide

## 🎯 **Overview**

ONOTE now features a **page-based desktop architecture** similar to Pages, Word, or Finale. This provides a modern, intuitive interface for music notation editing.

## 🖥️ **Key Features**

### **1. Resizable Desktop**
- **Large Canvas**: Desktop can be resized independently of the music page
- **Scrollable Area**: Navigate around the desktop with scroll bars
- **Free Space**: Area around the page for floating dialogs and tools

### **2. Floating Music Page**
- **Fixed Size**: Page maintains A4-like dimensions (800x1100px)
- **Independent Zoom**: Page zooms in/out while desktop resizes
- **Movable**: Page can be repositioned on the desktop
- **Visual Feedback**: Different appearances for setup vs edit modes

### **3. Mode Transitions**
- **Setup Mode**: Light blue background with grid pattern
- **Edit Mode**: Clean white background for score editing
- **Smooth Transitions**: Visual feedback when switching modes

### **4. Floating Dialogs**
- **Form Widget**: Musical form controls float on desktop
- **Dockable**: Dialogs can be docked or floated
- **Repositionable**: Move dialogs anywhere on desktop

## 🚀 **How to Use**

### **Running from Cursor**

1. **Open Cursor**
2. **Press Ctrl+Shift+D** (Run and Debug)
3. **Select "ONOTE Page-Based Desktop (Simple)"**
4. **Click the green play button ▶️**

### **Running from Terminal**

```bash
# Simple launcher (recommended)
python run_multi_window.py

# Full launcher with checks
python launch_onote.py

# Direct launch
python src/main_multi_window.py
```

## 🎨 **Desktop Interface**

### **Page Controls**
- **Zoom In/Out**: Ctrl++ / Ctrl+- or View menu
- **Fit to Page**: Ctrl+0 to fit page to view
- **Move Page**: Click and drag the page on desktop
- **Resize Desktop**: Resize the window normally

### **Menu System**
- **File**: New, Open, Save, Save As, Close
- **View**: Zoom controls and page fitting
- **Score**: Score Setup, Full Score Options
- **Edit**: Undo, Redo, Cut, Copy, Paste
- **Tools**: Preferences
- **Help**: About ONOTE

### **Floating Elements**
- **Musical Form Widget**: Right-side dock widget
- **Dialogs**: Score Setup, Full Score Options, Preferences
- **Context Menus**: Right-click on page elements

## 🔧 **Technical Architecture**

### **Core Components**

1. **DesktopWindow**: Main window with graphics scene
2. **MusicPage**: QGraphicsItem representing the music page
3. **StaffView**: Embedded in page via QGraphicsProxyWidget
4. **FormWidget**: Floating dock widget
5. **ApplicationManager**: Manages multiple desktop windows

### **Graphics Scene**
- **Large Scene**: 4000x4000 pixel scene for desktop
- **Page Positioning**: Page centered on scene
- **Zoom Handling**: Page-level zoom with scale transformation
- **Event Handling**: Mouse and keyboard events routed to page

### **Mode System**
- **Setup Mode**: Blue background, grid pattern, setup UI
- **Edit Mode**: White background, clean score view
- **Mode Switching**: Signal-based transitions

## 📋 **Development Plan**

### **Phase 1: Core Architecture** ✅
- [x] Desktop window with graphics scene
- [x] Floating music page with zoom
- [x] Mode transitions (setup/edit)
- [x] Basic menu system
- [x] Floating form widget

### **Phase 2: Enhanced Features** 🚧
- [ ] Advanced zoom controls
- [ ] Page positioning and snapping
- [ ] Multiple page support
- [ ] Page templates and presets
- [ ] Enhanced dialog positioning

### **Phase 3: Advanced UI** 📋
- [ ] Custom themes and styling
- [ ] Workspace management
- [ ] Advanced dialog anchoring
- [ ] Context menus and shortcuts
- [ ] Accessibility features

### **Phase 4: Integration** 📋
- [ ] Full menu system migration
- [ ] Document management
- [ ] Export and print features
- [ ] Plugin system integration
- [ ] Performance optimization

## 🧪 **Testing**

### **Test Scripts**
```bash
# Test desktop architecture
python test_desktop_architecture.py

# Test multi-window functionality
python test_multi_window.py
```

### **Manual Testing**
1. **Page Zoom**: Test zoom in/out functionality
2. **Mode Switching**: Switch between setup and edit modes
3. **Window Management**: Create multiple desktop windows
4. **Dialog Positioning**: Move and dock floating dialogs
5. **Page Movement**: Drag page around desktop

## 🎯 **Benefits**

### **User Experience**
- **Intuitive**: Familiar page-based interface
- **Flexible**: Resizable desktop with floating elements
- **Professional**: Clean, modern appearance
- **Efficient**: Independent zoom and positioning

### **Development**
- **Modular**: Clear separation of concerns
- **Extensible**: Easy to add new features
- **Maintainable**: Clean architecture
- **Testable**: Comprehensive test coverage

## 🔮 **Future Enhancements**

### **Advanced Features**
- **Multiple Pages**: Support for multi-page scores
- **Page Templates**: Pre-designed page layouts
- **Custom Themes**: User-defined color schemes
- **Workspace Presets**: Save/restore desktop layouts

### **Integration**
- **Plugin System**: Extensible architecture
- **Cloud Sync**: Document synchronization
- **Collaboration**: Multi-user editing
- **Mobile Support**: Touch-optimized interface

---

## 📞 **Support**

For questions or issues with the page-based desktop architecture:

1. **Check the test scripts** for functionality verification
2. **Review the code** in `src/gui/desktop_window.py`
3. **Run diagnostics** with the test scripts
4. **Report issues** with detailed error messages

The page-based desktop architecture provides a solid foundation for modern music notation editing with ONOTE! 🎵 