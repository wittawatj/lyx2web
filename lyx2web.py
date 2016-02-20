import argparse
import datetime
import os 
import re
import subprocess
import sys
import time

def file2str(fpath):
    with open(fpath, 'r') as f:
        s = f.read()
    return s

def str2file(st, fpath):
    with open(fpath, 'w') as f:
        f.write(st)

def run_shell_cmd(cmd):
    """cmd is a string to be typed into a shell"""
    ret = subprocess.call(cmd, shell=True)
    return ret

def extract_latex_preamble(tex_str):
    si = tex_str.index('\\begin{document}')
    return tex_str[:si]

def parse_joint_latex(tex_str):
    """
    Parse .tex string into a different blog posts.
    Each section considered one blog post.

    Return [(section, content)] where section = section string and 
    content is all the remaining string until the next section or end of doc.
    """
    # clean up tex. Remove unnecessary commands at the end of string.    
    tex_str = re.sub(r'\\'+'end{document}', '', tex_str)
    tex_str = re.sub(r'\\'+'bibliography{.+?}', '', tex_str)
    tex_str = re.sub(r'\\'+'bibliographystyle{.+?}', '', tex_str)

    list_posts = []
    # character index
    prev_end_sec_ind = -1
    sec_content_start = -1
    sec_title = None
    for m in re.finditer(r'\\'+'section{(.+?)}\n\n', tex_str, re.DOTALL):
        prev_end_sec_ind = m.start()
        if sec_title is not None:
            # add to the list 
            assert sec_content_start >= 0
            sec_content = tex_str[sec_content_start:prev_end_sec_ind]
            list_posts.append((sec_title, sec_content))

        # beginning of a section 
        sec_title = m.group(1)
        sec_content_start = m.end()
    # add the last post 
    sec_content = tex_str[sec_content_start:]
    list_posts.append((sec_title, sec_content))
    return list_posts


def today_date():
    """
    Get today's date in yyyy-mm-dd format as a string.
    """
    today = datetime.date.today()
    date_str = '%d-%d-%d'%(today.year, today.month, today.day)
    return date_str


def normalize_file_name(fname):
    """
    Remove/replace characters in the string so that the string is suitable 
    to be used as a file name.
    """
    t = fname 
    t = re.sub('[^0-9A-Za-z_-]', '_', t )
    t = re.sub('_+', '_', t)
    return t

def parse_post_meta(raw_postmeta):
    """
    Parse meta-data of a post contained in the special latex command 
    \postmeta{...}.
    Example:
    \postmeta{
    Title: Compactness and Open Sets in $\mathbb{R}^{d}$ 
    Date: 2014-06-29 
    Tags: topology, compactness 
    Slug: compactness_open_sets  
    }

    Return a dictionary
    """
    lines = raw_postmeta.split('\n')
    D = {}
    for i, l in enumerate(lines):
        if l.strip() != '':
            colon_splits = l.split(':')
            key = colon_splits[0].strip()
            val = colon_splits[1].strip()
            D[key] = val
    return D


def extract_post_meta(tex):
    """
    Locate the first section of \postmeta{...} and return it.
    See the spec in parse_post_meta()
    """
    m = re.search('postmeta{(.+?)}\n', tex, re.DOTALL)
    if m:
        return m.group(1)
    return None

def main(src_fpath, dest_dir, cleanup=False):
    src_dir = os.path.dirname(src_fpath)
    fname = os.path.basename(src_fpath)
    fname_noext = fname[:-4]
    if fname.endswith('.lyx'):
        # convert .lyx to .tex 
        #run_shell_cmd(['lyx', '-e', 'pdflatex', src_fpath])
        run_shell_cmd('lyx -e pdflatex %s'%src_fpath)
        # output is in the same directory
        tex_out_fpath = os.path.join(src_dir, fname_noext+'.tex')
        assert os.path.isfile(tex_out_fpath)
    elif fname.endswith('.tex'):
        tex_out_fpath = src_fpath
    else:
        raise ValueError('Unknown extension type of src="%s"'%src_fpath)

    # convert to utf8 with iconv
    utf_temp = os.path.join(src_dir, fname_noext+'_utf8.tex')
    #run_shell_cmd(['iconv', '-f', 'iso8859-1', '-t', 'utf8', tex_out_fpath,
    #    '>', utf_temp])
    run_shell_cmd('iconv -f iso8859-1 -t utf8 %s > %s'%(tex_out_fpath, utf_temp))

    # replace \postmeta with postmeta so that pandoc does not remove it 
    utf_content = file2str(utf_temp)
    #utf_content = utf_content.replace('\postmeta', 'postmeta')
    # write it back 
    str2file(utf_content, utf_temp)
    preamble = extract_latex_preamble(utf_content)

    list_posts = parse_joint_latex(utf_content)
    for i, ti_content  in enumerate(list_posts):
        title, tex_content = ti_content
        print 'Processing post %d: %s'%(i+1, title)
        # make a .tex file for each post 
        post_tex = preamble + '\n \\begin{document}\n' + '\\section{'+title+'}\n\n' \
            + tex_content + '\n \end{document}\n'
        # locate \postmeta section 
        raw_postmeta = extract_post_meta(post_tex)
        if raw_postmeta is None:
            # postmeta not found. Make a new one. 
            slug = normalize_file_name(title).lower()
            meta_str = 'Title: %s\n Date: %s\n Tags: \n Slug: %s'\
                %(title, today_date(), slug)
        else:
            pm_dict = parse_post_meta(raw_postmeta)
            slug = pm_dict['Slug']
            meta_str = raw_postmeta

        # write .tex 
        posti_fpath = os.path.join(dest_dir, slug+'.tex')
        str2file(post_tex, posti_fpath)
        # convert to markdown with pandoc
        posti_md_fpath = os.path.join(dest_dir, slug+'.md')
        run_shell_cmd('pandoc -s %s -o %s'%(posti_fpath, posti_md_fpath))

        # add the post meta data to the markdown file 
        md_content = file2str(posti_md_fpath)
        md_content = meta_str + '\n\n' + md_content
        str2file(md_content, posti_md_fpath)

    # clean up intermediate files


def validate_args(parsed):
    """
    Check the validity of each option value in the dict
    """
    src = parsed['src']
    dest = parsed['dest']
    if not os.path.isfile(src):
        raise ValueError('src="%s" is not a file'%src)
    if not (src.endswith('.tex') or src.endswith('.lyx')):
        raise ValueError('src="%s" is not a .lyx or .tex file'%src)
    if not os.path.isdir(dest):
        try:
            os.makedirs(dest)
        except:
            pass
    if not os.path.isdir(dest):
        raise ValueError('dest="%s" is not a directory'%dest)

if __name__ == '__main__':
    howto = """
    """
    parser = argparse.ArgumentParser(description='Convert a .tex or .lyx file \
            into a sequence of markdown files. Save them into the specified dest \
            directory. %s'%howto)
    parser.add_argument('src', help='Path to source file to be converted.')
    parser.add_argument('dest', help='Destination directory to save exported \
            markdown files.')

    parsed = parser.parse_args(sys.argv[1:])
    # A dict 
    parsed = vars(parsed)
    #print parsed
    validate_args(parsed)

    main(parsed['src'], parsed['dest'])


#===========================================

def parse_joint_markdown(md_str):
    """
    Parse markdown string into a different blog posts.
    The markdown string is obtained from pandoc. 
    Each section (denoted by =====) is considered one blog post.

    Return [(section, content)] where section = section string and 
    content is all the remaining string until the next section or end of doc.

    This method does not work with footnote as all the footnotes will be put 
    at the end of the document.
    """
    list_posts = []
    # each element does not contain \n at the end
    lines = md_str.split('\n')
    # line index
    prev_end_sec_ind = -1
    sec_content_start = -1
    sec_title = None
    for i, l in enumerate(lines):
        if l.startswith('========'):
            prev_end_sec_ind = i-1
            if sec_title is not None:
                # add to the list 
                assert sec_content_start >= 0
                sec_content = '\n'.join(lines[sec_content_start:prev_end_sec_ind])
                list_posts.append((sec_title, sec_content))

            # beginning of a section
            sec_title = lines[i-1]
            sec_content_start = i+1
    # add the last post 
    sec_content = '\n'.join(lines[sec_content_start:])
    list_posts.append((sec_title, sec_content))
    return list_posts
