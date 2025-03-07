from itertools import chain
import re
import math
from typing import Optional, Union
import pytesseract
from PIL import Image

from util import (
    indent_multiline,
    filter_meta_data,
    split_data_by_rank,
    error_correction_map,
    pattern_map,
    INDENT_ROUNDING,
)
from drawing import DrawingBoard, get_current_drawing_board, set_current_drawing_board
from spellchecker import SpellChecker

spell = SpellChecker("en")
_do_spell_check = False
_do_indent_check = False

class TesseractMetaData:
    def __init__(self, data):
        self.width = data["width"][0]
        self.height = data["height"][0]
        self.top = data["top"][0]
        self.left = data["left"][0]
        
    def __str__(self):
        return f"X={self.left}|Y={self.top}|W={self.width}|H={self.height}"

class TesseractBase:
    members: list
    meta: TesseractMetaData

    def __len__(self):
        return len(self.members)
    
    def __getitem__(self, i):
        return self.members[i]

    def __setitem__(self, i, val):
        self.members[i] = val
    
    def __delitem__(self, i):
        del self.members[i]

    def filter_empty(self):
        self.members = [i for i in self.members if len(i) > 0]

    def __repr__(self):
        s_members = [ indent_multiline(repr(i)) for i in self.members]
        s_members = "\n".join(s_members)
        return f"{type(self).__name__}(meta={self.meta}) \n{s_members}"

class TesseractWord:
    def __init__(self, data):
        self.text = data["text"][0]
        self.text = error_correction_map.get(self.text, self.text) # TODO:
        self.conf = data["conf"][0]
        self.meta = TesseractMetaData(data)

        # text = re.findall(r"\b[a-zA-Z]+(?:['-][a-zA-Z]+)*\b", self.text.lower())
        if not _do_spell_check:
            return

        if not any( re.match(p, self.text) is not None for p in pattern_map ):
            get_current_drawing_board().set_font_size(self.meta.height * 0.8)
            text = re.findall(r"\b[a-zA-Z]+(?:['-][a-zA-Z]+)*\.?\b", self.text.lower())
            misspelled = spell.unknown(text)    
            for word in misspelled:
                get_current_drawing_board().add_rounded_rectangle(
                    self.meta.left - 3,
                    self.meta.top - 1,
                    self.meta.width + 6,
                    self.meta.height + 2,
                    outline_color="blue",
                    border_width=2,
                    radius=5
                )
                # corrections = ", ".join(spell.correction(word))
                candidates = spell.candidates(word)
                if candidates is not None:
                    cand_text = ", ".join(list(candidates)[:3])
                    get_current_drawing_board().add_text(
                        self.meta.left,
                        self.meta.top - self.meta.height,
                        cand_text,
                        color="blue"
                    )
                    # print(word, cand_text)
        

    def __len__(self):
        return 1
    
    # @staticmethod
    # def split_words(word: "TesseractWord"):
    #     if word.text

    def as_str(self):
        return self.text
    
    def __repr__(self):
        return f"TesseractWord(meta={self.meta}, word={self.text}, conf={round(self.conf, 2)})"

class TesseractLine(TesseractBase):
    def __init__(self, data):
        meta = TesseractMetaData(data)
        data = filter_meta_data(data)
        words = split_data_by_rank(data, "word_num")
        self.members = [TesseractWord(i) for i in words]
        
        if len(self.members) == 0:
            self.meta = meta
        else:
            left = self.members[0].meta.left
            top = self.members[0].meta.top
            height = max(m.meta.height for m in self.members)
            width = max(m.meta.left + m.meta.width for m in self.members) - left
            self.meta = TesseractMetaData({
                "top": [top],
                "left": [left],
                "height": [height],
                "width": [width],
            })
            
        self.data = data
        self.filter_empty()


    @property
    def words(self):
        return self.members

    def as_str(self):
        return " ".join(w.as_str() for w in self.words)
    
class TesseractPar(TesseractBase):
    def __init__(self, data):
        self.meta = TesseractMetaData(data)
        data = filter_meta_data(data)
        lines = split_data_by_rank(data, "line_num")
        self.members = [TesseractLine(i) for i in lines]
        self.data = data
        self.filter_empty()

    @property
    def lines(self):
        return self.members
    
    @property
    def words(self):
        return list(chain(*[i.words for i in self.members]))

    def as_str(self):
        return "\n".join(w.as_str() for w in self.lines if len(w) > 0)

class TesseractBlock(TesseractBase):
    def __init__(self, data):
        self.meta = TesseractMetaData(data)
        data = filter_meta_data(data)
        pars = split_data_by_rank(data, "par_num")
        self.members = [TesseractPar(i) for i in pars]
        self.data = data
        self.filter_empty()
        
    @property
    def pars(self):
        return self.members
    
    @property
    def lines(self):
        return list(chain(*[i.lines for i in self.members]))
    
    @property
    def words(self):
        return list(chain(*[i.words for i in self.members]))

    def as_str(self):
        return "\n".join(w.as_str() for w in self.pars if len(w) > 0)

class TesseractPage(TesseractBase):
    def __init__(self, data):
        self.meta = TesseractMetaData(data)
        data = filter_meta_data(data)
        blocks = split_data_by_rank(data, "block_num")
        self.members = [TesseractBlock(i) for i in blocks]
        self.data = data
        self.filter_empty()

    @property
    def blocks(self):
        return self.members
    
    @property
    def pars(self):
        return list(chain(*[i.pars for i in self.members]))
    
    @property
    def lines(self):
        return list(chain(*[i.lines for i in self.members]))
    
    @property
    def words(self):
        return list(chain(*[i.words for i in self.members]))

    def as_str(self):
        return "\n\n".join(w.as_str() for w in self.blocks if len(w) > 0)

class TesseractArticle(TesseractBase):
    def __init__(self, data):
        # print(len(data["text"]))
        self.meta = TesseractMetaData(data)
        # data = filter_meta_data(data)
        # print(data) 
        pages = split_data_by_rank(data, "page_num")
        # print(pages)
        self.members = [TesseractPage(page) for page in pages]
        self.data = data
        self.filter_empty()

    @property
    def pages(self):
        return self.members
    
    @property
    def blocks(self):
        return list(chain(*[i.blocks for i in self.members]))
    
    @property
    def pars(self):
        return list(chain(*[i.pars for i in self.members]))
    
    @property
    def lines(self):
        return list(chain(*[i.lines for i in self.members]))
    
    @property
    def words(self):
        return list(chain(*[i.words for i in self.members]))

    def as_str(self):
        return "\n === Page === \n".join(w.as_str() for w in self.pages if len(w) > 0)

class Line:
    def __init__(self, line: TesseractLine):
        assert isinstance(line, TesseractLine)
        line_str = line.as_str().lstrip() 
        matches = [(pat, re.search(pat, line_str)) for pat in pattern_map]
        matches = [(pat, match.groups()[0]) for pat, match in matches if match is not None]
        matches = {pat: val for pat, val in matches}
        self.matches = matches
        self.line = line

    @property
    def patterns(self):
        return self.matches.keys()
    
    @property
    def values(self):
        return self.matches.values()

    def has_series_tag(self):
        return len(self.matches) > 0

    @property
    def meta(self):
        return self.line.meta

    def __repr__(self):
        return f"{self.matches}"
    
    def as_str(self):
        return self.line.as_str()

class Paragraph:
    def __init__(self, lines: list[Line]):
        self.lines = lines

        if len(lines) == 0:
            width = 0
            height = 0
            top = 0
            left = 0
        else:
            width = max(l.meta.width for l in lines)
            top = lines[0].meta.top
            left = lines[0].meta.left
            last_line_bottom = lines[-1].meta.top + lines[-1].meta.height
            height = last_line_bottom - top

        self._meta = TesseractMetaData({
            "width": [ width ],
            "height": [ height ],
            "top": [ top ],
            "left": [ left ],
        })

    @property
    def is_empty(self):
        return len(self.lines) == 0
    
    @property
    def patterns(self):
        assert len(self.lines) > 0
        return self.lines[0].patterns
    
    @property
    def values(self):
        assert len(self.lines) > 0
        return self.lines[0].values
    
    @property
    def matches(self):
        assert len(self.lines) > 0
        return self.lines[0].matches
    
    @matches.setter
    def matches(self, new):
        assert len(self.lines) > 0
        self.lines[0].matches = new

    @property
    def meta(self):
        return self._meta

    @property
    def indent(self):
        return math.floor(self.meta.left / INDENT_ROUNDING) * INDENT_ROUNDING

    def has_series_tag(self):
        assert len(self.lines) > 0
        return self.lines[0].has_series_tag()
    
    def as_str(self):
        if len(self.lines) == 0:
            return ""
        return "\n".join(line.as_str() for line in self.lines)
    
    @staticmethod   
    def group_paragraphs(lines: list[Line]) -> list["Paragraph"]:
        pars = []
        this_par = []
        for l in lines:
            if l.has_series_tag() or len(pars) == 0:
                if len(this_par) > 0:
                    pars.append(Paragraph(this_par))
                this_par = [l]
            else:
                this_par.append(l)
        pars.append(Paragraph(this_par))
        return pars

class Series:
    def __init__(self, par: Paragraph, members: Optional[list["Series"]] = None):
        self.par = par
        self.members = []
        if members is not None:
            for m in members:
                self.add(m)

    def __len__(self):
        return len(self.members)

    @property
    def indent(self):
        return self.par.indent

    @property
    def patterns(self):
        return self.par.patterns
    
    @property
    def values(self):
        return self.par.values
    
    @property
    def matches(self):
        return self.par.matches
    
    @matches.setter
    def matches(self, matches):
        self.par.matches = matches
    
    @property
    def member_patterns(self):
        if len(self) == 0:
            return None
        return self.members[-1].patterns
    
    @property
    def member_values(self):
        if len(self) == 0:
            return None
        return self.members[-1].values
    
    @property
    def member_matches(self):
        if len(self) == 0:
            return None
        return self.members[-1].matches
    
    @property
    def ranks(self):
        return [ pattern_map[p][0][v] for p, v in self.matches.items()]

    @member_matches.setter
    def member_matches(self, new_member_matches):
        if len(self) == 0:
            return # TODO: maybe raise error because you aren't suppose to set this without members
        assert len(self) == len(new_member_matches)
        for m, n in zip(self.members, new_member_matches):
            m.matches = n

    def expects(self):
        rank_maps = [pattern_map[p][1] for p in self.patterns]
        expected = [  None if r >= len(m) else list(m)[r + 1] for m, r in zip(rank_maps, self.ranks)]
        return expected

    def check(self):
        if len(self) == 0:
            return True
        # if self.par.is_empty:
        #     return True
        
        initial_expects = [v[1][0] for v in pattern_map.values()]
        # pivot = self.members[0]
        prev_mem = None

        for mem_idx, mem in enumerate(self.members):
            mem.check()
            is_expected = False
            if prev_mem is None:
                prev_mem_expects = initial_expects
            else:
                prev_mem_expects = prev_mem.expects()

            if len(mem.values) == 0 and (mem_idx == 0 or len(prev_mem_expects) == 0):
                is_expected = True
            else:
                for v in mem.values:
                    if v in prev_mem_expects:
                        # pivot expects this thing
                        is_expected = True
                        break
            mem_par = mem.par
            mem_meta = mem.par.meta
            if prev_mem is None:
                prev_mem_meta = mem_meta
                prev_mem_par = mem_par
            else:
                prev_mem_meta = prev_mem.par.meta
                prev_mem_par = prev_mem.par
            height = mem_meta.top + mem_meta.height - prev_mem_meta.top
            db = get_current_drawing_board()
            if not is_expected:
                db.add_verticle_line(prev_mem_meta.left, prev_mem_meta.top, height, "red", 6)
                db.add_horizontal_line(prev_mem_meta.left, mem_meta.top-2, db.width - prev_mem_meta.left, "red", 3)
                font_size = int(prev_mem_par.lines[0].meta.height * 0.8)
                db.set_font_size( font_size  )
                prev_mem_expects_str = ", ".join(f"({str(i)})" for i in prev_mem_expects)
                mem_values_str = ", ".join( f"({str(i)})" for i in mem.values)
                if len(prev_mem_expects) == 1:
                    text = f"expected {prev_mem_expects_str}, but got {mem_values_str}"
                else:
                    text = f"expected one of {prev_mem_expects_str}, but got {mem_values_str}"
                db.add_text(prev_mem_meta.left + 25, mem_meta.top - font_size - 6, text, "red")

                print(f"expected one of {prev_mem_expects_str}, but got {mem.values}")
            else:
                db.add_verticle_line(prev_mem_meta.left, prev_mem_meta.top, height, "green", 2)
                print(f"CONGRATS! expected one of {prev_mem_expects}, got {mem.values}")
            prev_mem = mem


    def add(self, new_member: Union["Series", Paragraph]):
        if isinstance(new_member, Paragraph):
            new_member = Series(new_member)
        self.members.append(new_member)

    def as_str(self):
        if self.par.is_empty:
            return "\n".join( m.as_str() for m in self.members )
        s_members = [ indent_multiline(m.as_str()) for m in self.members]
        s_members = "\n".join(s_members)
        s_head = self.par.as_str()
        return s_head + "\n" + s_members



def process(image: Image, lang="eng", indent_check=False, spell_check=False):
    # Perform OCR to get detailed text data as a dictionary
    set_current_drawing_board(DrawingBoard(image.copy()))
    data = pytesseract.image_to_data(image, output_type='dict', lang=lang)

    # global _indent_check 
    global _do_spell_check
    global _do_indent_check
    _do_spell_check = spell_check
    _do_indent_check = indent_check

    article = TesseractArticle(data)    
    lines = [Line(l) for l in article.lines]
    pars = Paragraph.group_paragraphs(lines)
   
    def group_nest(pars: list[Paragraph]):
        if len(pars) == 0:
            return []
        target_indent = min(p.indent for p in pars)
        nest_members = []
        head_par = pars[0]
        sub_pars = []
        for p in pars[1:]:
            if p.indent > target_indent:
                sub_pars.append(p)
            elif p.indent == target_indent:
                member = Series(head_par, group_nest(sub_pars))
                nest_members.append( member )
                sub_pars = []
                head_par = p
            else:
                break

        last_member = Series(head_par, group_nest(sub_pars))
        nest_members.append( last_member )

        return nest_members
    
    # NOTE: Recursively group paragraphs into a hierarchy
    s = Series(Paragraph([]), group_nest(pars))
        
    # NOTE: Checking alignment
    if _do_indent_check:
        s.check()
    get_current_drawing_board().image#.show()
    return get_current_drawing_board().image, s, article
