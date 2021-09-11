---
layout: posts
title: IntelliJ Tips
tags:
- java
- intelliJ
---
# Shortcuts
## Expand/collapse method body in code editor
`Cmd + +/-` to expand and collapse a method body
## Show java doc
- Ctrl+J: To show JavaDoc

- Cmd+Alt+B: To show interface implementations
- Alt+Enter: when cursor on class declare line, press Alt+Enter can quickly create a unit test against this test class



- Ctrl+Shift+A: Action window, just like sublime, search IDE actions
- F11: add bookmark,
- Shift+F11: show bookmarks
- Shift + Escape: close bottom source pannel or left side barGo to settings, Editor->General->Mouse-> change font size (Zoom)
- Alt + F: Git refresh : Assign it in Intellij key map
- Ctrl + T: swich different editorsAlt + F1: Show in , then preses '1' to show file in project viewer, like "scroll from source"use Ctrl+Q to show quick documentation for the element at caret. to show javadocAlt + F12: to open terminal window, then 'mvn package'
- Ctrl+I: implement methodsAlt+A: code completion, this is customized in keymap, for 'basic'Press Tab / Shift+Tab. To change indentation of a text fragmentCtrl+Alt+I To fix indentationCtrl+D  Duplicate Line or SelectionAlt + Insert: generate code (getter or setter, toString)Ctrl+F12: List all opened files, press Enter to selectAlt+1: to show the project tree window, press Alt+1 again will close the project structureAlt+7: show structureGo to interface implementations, the shortcut In PC, it is CTRL + ALT + B: JetBrains navigation documentation.
- maximize edito pane: Ctrl + Shift + F12 (Default keymap).- Ctrl+R: repalce- F6: move file, Shift+F6: rename file- Ctrl+Alt+ <-: go back to previous position- Ctrl+Alt+S: show settings- bookmakr: F11 toggle for annonymous bookmark, Shift+F11: show all bookmarks. Ctrl+F11: then press 0,1,2,3, etc. then Ctrl +1, Ctrl +3, to go to that bookmarkmaster password: hello123- copy file name: focus file in "project view", press Ctrl+C- Incremental search: Ctrl+F, then use up/down arrow keys to navigate- Ctrl+Shift+N: open files by file name pattern- Press Ctrl+Shift+B . Press the Ctrl+Shift keys and hover your mouse pointer over the symbol. When the symbol turns to a hyperlink, click it without releasing Ctrl+Shift keys. The type declaration of the symbol opens in the editor.
- Ctrl+Shift+F7: highlight all references (of selected method)
put carpet on a name, Ctrl+B will show the definition
Ctrl+Shift+Alt+F: copy current file name
-- go to matching braceCtrl+} will move to the close bracket.Ctrl+{ will move to the open bracket
-- split editorgo to menu "window" -> "editor tabs" -> split
Firslty open wealth-access-ui project, which only contains files at root, then right click in left pane, and chose import wealth-acecss-ui, it will load module.Use F2/Shift+F2 keys to jump between highlighted syntax errors.Use Ctrl+Alt+Up/Ctrl+Alt+Down shortcuts to jump between compiler error messages or search operation results.Use Ctrl+J to complete any valid Live Template abbreviation if you don't remember it. For example, type it and press Ctrl+J to see what happens.

- Navigating to the declaration of a symbol
Place the caret at the desired symbol in the editor.Do one of the following:On the main menu, choose Navigate | Declaration.Press Ctrl+B.Click the middle mouse button.Keeping Ctrl pressed, point to the symbol, and click, when it turns to a hyperlink. You can also see declaration at the tooltip while keeping Ctrl pressed.


Ctrl+Shift+A: Action window, just like sublime, search IDE actions
F11: add bookmark, 
Shift+F11: show bookmarks
Shift + Escape: close bottom source pannel or left side bar
Go to settings, Editor->General->Mouse-> change font size (Zoom)
Alt + F: Git refresh : Assign it in Intellij key map
Ctrl + T: swich different editors
Alt + F1: Show in , then preses '1' to show file in project viewer, like "scroll from source"
use Ctrl+Q to show quick documentation for the element at caret. to show javadoc
Alt + F12: to open terminal window, then 'mvn package'
Ctrl+I: implement methods
Alt+A: code completion, this is customized in keymap, for 'basic'
Press Tab / Shift+Tab. To change indentation of a text fragment
Ctrl+Alt+I To fix indentation
Ctrl+D  Duplicate Line or Selection
Alt + Insert: generate code (getter or setter, toString)
Ctrl+F12: List all opened files, press Enter to select
Alt+1: to show the project tree window, press Alt+1 again will close the project structure
Alt+7: show structure
Go to interface implementations, the shortcut In PC, it is CTRL + ALT + B: JetBrains navigation documentation.

- maximize edito pane: Ctrl + Shift + F12 (Default keymap).
- Ctrl+R: repalce
- F6: move file, Shift+F6: rename file
- Ctrl+Alt+ <-: go back to previous position
- Ctrl+Alt+S: show settings
- bookmakr: F11 toggle for annonymous bookmark, Shift+F11: show all bookmarks. Ctrl+F11: then press 0,1,2,3, etc. then Ctrl +1, Ctrl +3, to go to that bookmark
master password: hello123
- copy file name: focus file in "project view", press Ctrl+C
- Incremental search: Ctrl+F, then use up/down arrow keys to navigate
- Ctrl+Shift+N: open files by file name pattern
- Press Ctrl+Shift+B . Press the Ctrl+Shift keys and hover your mouse pointer over the symbol. When the symbol turns to a hyperlink, click it without releasing Ctrl+Shift keys. The type declaration of the symbol opens in the editor.

- Ctrl+Shift+F7: highlight all references (of selected method)


put carpet on a name, Ctrl+B will show the definition

Ctrl+Shift+Alt+F: copy current file name

-- go to matching brace
Ctrl+} will move to the close bracket.
Ctrl+{ will move to the open bracket


-- split editor
go to menu "window" -> "editor tabs" -> split

Firslty open wealth-access-ui project, which only contains files at root, then right click in left pane, and chose import wealth-acecss-ui, it will load module.
Use F2/Shift+F2 keys to jump between highlighted syntax errors.
Use Ctrl+Alt+Up/Ctrl+Alt+Down shortcuts to jump between compiler error messages or search operation results.
Use Ctrl+J to complete any valid Live Template abbreviation if you don't remember it. For example, type it and press Ctrl+J to see what happens.



- Navigating to the declaration of a symbol

Place the caret at the desired symbol in the editor.
Do one of the following:
On the main menu, choose Navigate | Declaration.
Press Ctrl+B.
Click the middle mouse button.
Keeping Ctrl pressed, point to the symbol, and click, when it turns to a hyperlink. You can also see declaration at the tooltip while keeping Ctrl pressed.


By defining a Scope when searching, you can include/exclude arbitrary files/folders from that scope.
Detailed Answer
One way to achieve your requirement (excluding files and folders from a search) is to define a custom scope. This is specifically useful because sometimes you just want to exclude a folder from your search and not from the whole project.
Follow these steps:
Edit -> Find -> Find in path or press Ctrl+Shift+F.Choose Custom in the Scope section and then choose <unknown scope>


## how to add xx-properties project to xx project as dependencies
select project and press F4 to open properites, chose 'module' in left pane and then click "+", chose 'import module', then chose the properties project


# Intelij classes

## Annotation Nullable
```java
/*
 * Copyright 2000-2009 JetBrains s.r.o.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.jetbrains.annotations;

import java.lang.annotation.*;

/**
 * An element annotated with Nullable claims <code>null</code> value is perfectly <em>valid</em>
 * to return (for methods), pass to (parameters) and hold (local variables and fields).
 * Apart from documentation purposes this annotation is intended to be used by static analysis tools
 * to validate against probable runtime errors and element contract violations.
 * @author max
 */
@Documented
@Retention(RetentionPolicy.CLASS)
@Target({ElementType.METHOD, ElementType.FIELD, ElementType.PARAMETER, ElementType.LOCAL_VARIABLE})
public @interface Nullable {
  String value() default "";
}
```
