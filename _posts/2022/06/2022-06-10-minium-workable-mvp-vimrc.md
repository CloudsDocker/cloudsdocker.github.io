"----------------------------------------------------------------
" 4. User interface
"----------------------------------------------------------------
" Set X lines to the cursor when moving vertically
set scrolloff=0

" Always show mode
set showmode

" Show command keys pressed
set showcmd

" Enable the WiLd menu
set wildmenu

" Show the current position
set ruler

" Command bar height
set cmdheight=2

" Backspace works on Insert mode
set backspace=eol,start,indent

" Don't redraw while executing macros (good performance config)
set lazyredraw

" Show matching brackets when text indicator is over them
set showmatch

" How many tenths of a second to blink when matching brackets
set matchtime=2

" No annoying sound on errors
set noerrorbells
set novisualbell


" Mouse
set mouse=a

" Highlight cursor line and cursor column
set cursorline
set nocursorcolumn

" Always show the status line
set laststatus=2

" Change the cursor shape
if !has("nvim")
	let &t_SI = "\<Esc>[6 q"
	let &t_SR = "\<Esc>[4 q"
	let &t_EI = "\<Esc>[2 q"
else
	set guicursor=n-v:block-Cursor/lCursor-blinkon0
	set guicursor+=i-ci-c:ver100-Cursor/lCursor-blinkon0
	set guicursor+=r-cr:hor100-Cursor/lCursor-blinkon0
endif

" Omni completion
if has('autocmd') && exists('+omnifunc')
autocmd Filetype *
	\ if &omnifunc == "" |
	\     setlocal omnifunc=syntaxcomplete#Complete |
	\ endif
endif

" Fix italics issue
if !has("nvim")
	let &t_ZH="\e[3m"
	let &t_ZR="\e[23m"
endif

"----------------------------------------------------------------
" 5. Scheme and colors
"----------------------------------------------------------------
" True color
" if !has("nvim")
"   if has("termguicolors")
"       let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
"       let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
"       set termguicolors
"   endif
" else
"   set termguicolors
" endif

" Syntax highlighting
syntax enable

" Color scheme
colorscheme atomic

" Show syntax highlighting groups
nnoremap <Leader>B :call <SID>SynStack()<CR>

"----------------------------------------------------------------
" 6. Files and backup
"----------------------------------------------------------------
" Disable swap files
set noswapfile

" No backup (use Git instead)
set nobackup

" Prevents automatic write backup
set nowritebackup

" Use UTF-8 as default encoding
set encoding=utf8

" Use Unix as the standard file type
set fileformats=unix,dos,mac

" Autoread a file when it is changed from the outside
set autoread

" Reload a file when it is changed from the outside
let g:f5msg = 'Buffer reloaded.'
nnoremap <F5> :e<CR>:echo g:f5msg<CR>

" Enable filetype plugins
filetype plugin on
filetype indent on

" Allow us to use Ctrl-s and Ctrl-q as keybinds
" Restore default behaviour when leaving Vim.
if !has("nvim")
	silent !stty -ixon
	autocmd VimLeave * silent !stty ixon
endif

" Save the current buffer
nnoremap <Leader>s :update<CR>

" Save all buffers
nnoremap <Leader>S :bufdo update<CR>

" :W sudo saves the file
" (useful for handling the permission-denied error)
cnoremap WW w !sudo tee > /dev/null %

" Rename file
nnoremap <F2> :call <SID>RenameFile()<CR>

" Work on buffer
nnoremap yab :%y<CR>
nnoremap dab :%d<CR>
nnoremap vab ggVG

"----------------------------------------------------------------
" 7. Buffers management
"----------------------------------------------------------------
" Buffer hidden when it is abandoned
set hidden

" Close the current buffer
nnoremap <Leader>bd :call <SID>CustomCloseBuffer()<CR>

" Move between buffers
nnoremap <C-h> :bprev<CR>
nnoremap <C-l> :bnext<CR>

" Edit and explore buffers
nnoremap <Leader>bb :edit <C-R>=expand("%:p:h")<CR>/
nnoremap <Leader>bg :buffers<CR>:buffer<Space>

" Switch CWD to the directory of the current buffer
nnoremap <Leader>bw :lcd %:p:h<CR>:pwd<CR>

" Copy the filepath to clipboard
nnoremap <Leader>by :let @+=expand("%:p")<CR>

" Ignore case when autocompletes when browsing files
set fileignorecase

" Specify the behavior when switching between buffers
try
	set switchbuf=useopen,usetab,newtab
	set showtabline=2
catch
endtry

" Remember info about open buffers on close
" set viminfo^=%

"----------------------------------------------------------------
" 8. Tabs management
"----------------------------------------------------------------
" Create and close tabs
nnoremap <Leader>td :tabclose<CR>
nnoremap <Leader>to :tabonly<CR>

" Open a new tab with the current buffer's path
" Useful when editing files in the same directory
nnoremap <Leader>tt :tabedit <C-R>=expand("%:p:h")<CR>/

" Move tabs position
nnoremap <Leader>tr :execute 'silent! tabmove ' . (tabpagenr()-2)<CR>
nnoremap <Leader>ty :execute 'silent! tabmove ' . tabpagenr()<CR>

"----------------------------------------------------------------
" 9. Multiple windows
"----------------------------------------------------------------
" Remap wincmd
map <Leader>, <C-w>

set winminheight=0
set winminwidth=0
set splitbelow
set splitright
set fillchars+=stlnc:\/,vert:│,fold:―,diff:―

" Split windows
map <C-w>- :split<CR>
map <C-w>. :vsplit<CR>
map <C-w>j :close<CR>
map <C-w>x :q!<CR>
map <C-w>, <C-w>=

" Resize windows
if bufwinnr(1)
	map + :resize +1<CR>
	map - :resize -1<CR>
	map < :vertical resize +1<CR>
	map > :vertical resize -1<CR>
endif

" Toggle resize window
nnoremap <silent> <C-w>f :call <SID>ToggleResize()<CR>

" Last, previous and next window; and only one window
nnoremap <silent> <C-w>l :wincmd p<CR>:echo "Last window."<CR>
nnoremap <silent> <C-w>p :wincmd w<CR>:echo "Previous window."<CR>
nnoremap <silent> <C-w>n :wincmd W<CR>:echo "Next window."<CR>
nnoremap <silent> <C-w>o :wincmd o<CR>:echo "Only one window."<CR>

" Move between Vim windows and Tmux panes
" - It requires the corresponding configuration into Tmux.
" - Check it at my .tmux.conf from my dotfiles repository.
" - URL: https://github.com/gerardbm/dotfiles/blob/master/tmux/.tmux.conf
" - Plugin required: https://github.com/christoomey/vim-tmux-navigator
if !has("nvim")
	set <M-h>=h
	set <M-j>=j
	set <M-k>=k
	set <M-l>=l
endif

nnoremap <silent> <M-h> :TmuxNavigateLeft<CR>
nnoremap <silent> <M-j> :TmuxNavigateDown<CR>
nnoremap <silent> <M-k> :TmuxNavigateUp<CR>
nnoremap <silent> <M-l> :TmuxNavigateRight<CR>

" Remove the Windows ^M - when the encodings gets messed up
noremap <Leader><BS> mmHmt:%s/<C-v><CR>//ge<CR>'tzt`m

" Close the preview window
nnoremap <silent> <Leader>. :pclose<CR>

" Scroll the preview window
if !has("nvim")
	set <M-d>=d
	set <M-u>=u
endif

nnoremap <silent> <M-d> :wincmd P<CR>5<C-e>:wincmd p<CR>
nnoremap <silent> <M-u> :wincmd P<CR>5<C-y>:wincmd p<CR>

"----------------------------------------------------------------
" 10. Indentation tabs
"----------------------------------------------------------------
" Enable autoindent & smartindent
set autoindent
set smartindent

" Use tabs, no spaces
set noexpandtab

" Be smart when using tabs
set smarttab

" Tab size (in spaces)
set shiftwidth=2
set tabstop=2

" Remap indentation
nnoremap <TAB> >>
nnoremap <S-TAB> <<

vnoremap <TAB> >gv
vnoremap <S-TAB> <gv

inoremap <TAB> <C-i>
inoremap <S-TAB> <C-d>

" Don't show tabs
set list

let g:f6msg = 'Toggle list.'
nnoremap <F6> :set list!<CR>:echo g:f6msg<CR>

" Show tabs and end-of-lines
set listchars=tab:│\ ,trail:¬

"----------------------------------------------------------------
" 11. Moving around lines
"----------------------------------------------------------------
" Specify which commands wrap to another line
set whichwrap+=<,>,h,l

" Many jump commands move the cursor to the start of line
set nostartofline

" Wrap lines into the window
set wrap

" Don't break the words
" Only works if I set nolist (F6)
set linebreak
set showbreak=├——»

" Stop automatic wrapping
set textwidth=0

" Column at 80 width
set colorcolumn=80

" Listings don't pause
set nomore

" Color column
let g:f10msg = 'Toggle colorcolumn.'
nnoremap <silent> <F10> :call <SID>ToggleColorColumn()<CR>:echo g:f10msg<CR>

" Show line numbers
set number
set numberwidth=2

let g:f3msg = 'Toggle line numbers.'
nnoremap <silent> <F3> :set number!<CR>:echo g:f3msg<CR>

" Set relative line numbers
set relativenumber

let g:f4msg = 'Toggle relative line numbers.'
nnoremap <silent> <F4> :set norelativenumber!<CR>:echo g:f4msg<CR>

" Treat long lines as break lines (useful when moving around in them)
nnoremap <silent> <expr> k (v:count == 0 ? 'gk' : 'k')
nnoremap <silent> <expr> j (v:count == 0 ? 'gj' : 'j')

vnoremap <silent> <expr> k (v:count == 0 ? 'gk' : 'k')
vnoremap <silent> <expr> j (v:count == 0 ? 'gj' : 'j')

nnoremap <Home> g^
nnoremap <End> g$

vnoremap <Home> g^
vnoremap <End> g$

" Toggle the cursor position start/end of the line
nnoremap <silent> ñ :call <SID>ToggleCPosition('')<CR>
vnoremap <silent> ñ <Esc>:call <SID>ToggleCPosition('normal! gv')<CR>

" Join / split lines
nnoremap <C-j> J
nnoremap <C-k> i<CR><Esc>

" Duplicate a line
nnoremap cx yyP
nnoremap cv yyp

" Folding
set foldmethod=marker

" Return to last edit position when opening files
autocmd BufReadPost *
	\ if line("'\"") > 0 && line("'\"") <= line("$") |
	\   exe "normal! g`\"" |
	\ endif

" --- Readline commands ---
"----------------------------------------------------------------
" Move the cursor to the line start
inoremap <C-a> <C-O>0

" Move the cursor to the line end
inoremap <C-e> <C-O>$

" Moves the cursor back one character
inoremap <expr><C-b> deoplete#smart_close_popup()."\<Left>"

" Moves the cursor forward one character
inoremap <expr><C-f> deoplete#smart_close_popup()."\<Right>"

" Remove one character
inoremap <C-d> <DEL>

" Command Mode
cnoremap <C-b> <Left>
cnoremap <C-f> <Right>
cnoremap <C-a> <Home>
cnoremap <C-e> <End>
cnoremap <C-d> <DEL>
cnoremap <C-p> <Up>
cnoremap <C-n> <Down>
cnoremap <C-v> <C-r>"
cnoremap <C-q> <S-Right><C-w>

"----------------------------------------------------------------
" 12. Paste mode
"----------------------------------------------------------------
" Bracketed paste mode
" - Source: https://ttssh2.osdn.jp/manual/en/usage/tips/vim.html
if !has("nvim")
	if has("patch-8.0.0238")
		if &term =~ "screen"
			let &t_BE = "\e[?2004h"
			let &t_BD = "\e[?2004l"
			exec "set t_PS=\e[200~"
			exec "set t_PE=\e[201~"
		endif
	endif
endif

"----------------------------------------------------------------
" 13. Search, vimgrep and grep
"----------------------------------------------------------------
" Highlight search results
set hlsearch

" Makes search act like search in modern browsers
set incsearch

" Search, wrap around the end of the buffer
set wrapscan

" Ignore case when searching
set ignorecase

" When searching try to be smart about cases
set smartcase

" For regular expressions turn magic on
set magic

" Maximum amount of memory in Kbyte used for pattern matching
set maxmempattern=1000

" --- Highlight ---
"----------------------------------------------------------------
" Map <Space> to / (search)
nnoremap <Space> /
nnoremap <Leader><Space> ?

" Highlight the word under the cursor and don't jump to next
nnoremap <silent> <Leader><CR> :let @/='\<<C-R>=expand("<cword>")<CR>\>'<CR>:set hlsearch<CR>

" Highlight the selected text and don't jump to next
vnoremap <silent> <Leader><CR> :<C-U>call <SID>VSetSearch()<CR>:set hlsearch<CR>

" Disable highlight
nnoremap <Leader>m :noh<CR>

" Search into a Visual selection
vnoremap <silent> <Space> :<C-U>call <SID>RangeSearch('/')<CR>
	\ :if strlen(g:srchstr) > 0
	\ \|exec '/'.g:srchstr\|endif<CR>n
vnoremap <silent> ? :<C-U>call <SID>RangeSearch('?')<CR>
	\ :if strlen(g:srchstr) > 0
	\ \|exec '?'.g:srchstr\|endif<CR>N
