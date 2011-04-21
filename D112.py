#
# 10 Feb 2011
#

import sys
import getopt
import re as re_

etree_ = None
Verbose_import_ = False
(   XMLParser_import_none, XMLParser_import_lxml,
    XMLParser_import_elementtree
    ) = range(3)
XMLParser_import_library = None
try:
    # lxml
    from lxml import etree as etree_
    XMLParser_import_library = XMLParser_import_lxml
    if Verbose_import_:
        print("running with lxml.etree")
except ImportError:
    try:
        import xml.etree.cElementTree as etree_
        XMLParser_import_library = XMLParser_import_elementtree
        if Verbose_import_:
            print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            import xml.etree.ElementTree as etree_
            XMLParser_import_library = XMLParser_import_elementtree
            if Verbose_import_:
                print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                import cElementTree as etree_
                XMLParser_import_library = XMLParser_import_elementtree
                if Verbose_import_:
                    print("running with cElementTree")
            except ImportError:
                try:
                    import elementtree.ElementTree as etree_
                    XMLParser_import_library = XMLParser_import_elementtree
                    if Verbose_import_:
                        print("running with ElementTree")
                except ImportError:
                    raise ImportError("Failed to import ElementTree from any known place")

def parsexml_(*args, **kwargs):
    if (XMLParser_import_library == XMLParser_import_lxml and
        'parser' not in kwargs):
        kwargs['parser'] = etree_.ETCompatXMLParser()
    doc = etree_.parse(*args, **kwargs)
    return doc

#
# User methods
#


try:
    from generatedssuper import GeneratedsSuper
except ImportError, exp:

    class GeneratedsSuper(object):
        def gds_format_string(self, input_data, input_name=''):
            return input_data
        def gds_format_integer(self, input_data, input_name=''):
            return '%d' % input_data
        def gds_format_float(self, input_data, input_name=''):
            return '%f' % input_data
        def gds_format_double(self, input_data, input_name=''):
            return '%e' % input_data
        def gds_format_boolean(self, input_data, input_name=''):
            return '%s' % input_data
        def gds_str_lower(self, instring):
            return instring.lower()
                    
                    

#
# Globals
#

ExternalEncoding = 'ascii'
Tag_pattern_ = re_.compile(r'({.*})?(.*)')
STRING_CLEANUP_PAT = re_.compile(r"[\n\r\s]+")

#
# Support/utility functions.
#

def showIndent(outfile, level):
    for idx in range(level):
        outfile.write('    ')

def quote_xml(inStr):
    if not inStr:
        return ''
    s1 = (isinstance(inStr, basestring) and inStr or
          '%s' % inStr)
    s1 = s1.replace('&', '&amp;')
    s1 = s1.replace('<', '&lt;')
    s1 = s1.replace('>', '&gt;')
    return s1

def quote_attrib(inStr):
    s1 = (isinstance(inStr, basestring) and inStr or
          '%s' % inStr)
    s1 = s1.replace('&', '&amp;')
    s1 = s1.replace('<', '&lt;')
    s1 = s1.replace('>', '&gt;')
    if '"' in s1:
        if "'" in s1:
            s1 = '"%s"' % s1.replace('"', "&quot;")
        else:
            s1 = "'%s'" % s1
    else:
        s1 = '"%s"' % s1
    return s1

def quote_python(inStr):
    s1 = inStr
    if s1.find("'") == -1:
        if s1.find('\n') == -1:
            return "'%s'" % s1
        else:
            return "'''%s'''" % s1
    else:
        if s1.find('"') != -1:
            s1 = s1.replace('"', '\\"')
        if s1.find('\n') == -1:
            return '"%s"' % s1
        else:
            return '"""%s"""' % s1


def get_all_text_(node):
    if node.text is not None:
        text = node.text
    else:
        text = ''
    for child in node:
        if child.tail is not None:
            text += child.tail
    return text


class GDSParseError(Exception):
    pass

def raise_parse_error(node, msg):
    if XMLParser_import_library == XMLParser_import_lxml:
        msg = '%s (element %s/line %d)' % (msg, node.tag, node.sourceline, )
    else:
        msg = '%s (element %s)' % (msg, node.tag, )
    raise GDSParseError(msg)


class MixedContainer:
    # Constants for category:
    CategoryNone = 0
    CategoryText = 1
    CategorySimple = 2
    CategoryComplex = 3
    # Constants for content_type:
    TypeNone = 0
    TypeText = 1
    TypeString = 2
    TypeInteger = 3
    TypeFloat = 4
    TypeDecimal = 5
    TypeDouble = 6
    TypeBoolean = 7
    def __init__(self, category, content_type, name, value):
        self.category = category
        self.content_type = content_type
        self.name = name
        self.value = value
    def getCategory(self):
        return self.category
    def getContenttype(self, content_type):
        return self.content_type
    def getValue(self):
        return self.value
    def getName(self):
        return self.name
    def export(self, outfile, level, name, namespace):
        if self.category == MixedContainer.CategoryText:
            # Prevent exporting empty content as empty lines.
            if self.value.strip(): 
                outfile.write(self.value)
        elif self.category == MixedContainer.CategorySimple:
            self.exportSimple(outfile, level, name)
        else:    # category == MixedContainer.CategoryComplex
            self.value.export(outfile, level, namespace,name)
    def exportSimple(self, outfile, level, name):
        if self.content_type == MixedContainer.TypeString:
            outfile.write('<%s>%s</%s>' % (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeInteger or \
                self.content_type == MixedContainer.TypeBoolean:
            outfile.write('<%s>%d</%s>' % (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeFloat or \
                self.content_type == MixedContainer.TypeDecimal:
            outfile.write('<%s>%f</%s>' % (self.name, self.value, self.name))
        elif self.content_type == MixedContainer.TypeDouble:
            outfile.write('<%s>%g</%s>' % (self.name, self.value, self.name))
    def exportLiteral(self, outfile, level, name):
        if self.category == MixedContainer.CategoryText:
            showIndent(outfile, level)
            outfile.write('model_.MixedContainer(%d, %d, "%s", "%s"),\n' % \
                (self.category, self.content_type, self.name, self.value))
        elif self.category == MixedContainer.CategorySimple:
            showIndent(outfile, level)
            outfile.write('model_.MixedContainer(%d, %d, "%s", "%s"),\n' % \
                (self.category, self.content_type, self.name, self.value))
        else:    # category == MixedContainer.CategoryComplex
            showIndent(outfile, level)
            outfile.write('model_.MixedContainer(%d, %d, "%s",\n' % \
                (self.category, self.content_type, self.name,))
            self.value.exportLiteral(outfile, level + 1)
            showIndent(outfile, level)
            outfile.write(')\n')


class MemberSpec_(object):
    def __init__(self, name='', data_type='', container=0):
        self.name = name
        self.data_type = data_type
        self.container = container
    def set_name(self, name): self.name = name
    def get_name(self): return self.name
    def set_data_type(self, data_type): self.data_type = data_type
    def get_data_type_chain(self): return self.data_type
    def get_data_type(self):
        if isinstance(self.data_type, list):
            if len(self.data_type) > 0:
                return self.data_type[-1]
            else:
                return 'xs:string'
        else:
            return self.data_type
    def set_container(self, container): self.container = container
    def get_container(self): return self.container

def _cast(typ, value):
    if typ is None or value is None:
        return value
    return typ(value)

#
# Data representation classes.
#

class declaratieUnica(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, luna_r=None, d_rec='0', an_r=None, nume_declar=None, functie_declar=None, prenume_declar=None, angajator=None, asigurat=None):
        self.luna_r = _cast(None, luna_r)
        self.d_rec = _cast(None, d_rec)
        self.an_r = _cast(None, an_r)
        self.nume_declar = _cast(None, nume_declar)
        self.functie_declar = _cast(None, functie_declar)
        self.prenume_declar = _cast(None, prenume_declar)
        self.angajator = angajator
        if asigurat is None:
            self.asigurat = []
        else:
            self.asigurat = asigurat
    def factory(*args_, **kwargs_):
        if declaratieUnica.subclass:
            return declaratieUnica.subclass(*args_, **kwargs_)
        else:
            return declaratieUnica(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_angajator(self): return self.angajator
    def set_angajator(self, angajator): self.angajator = angajator
    def get_asigurat(self): return self.asigurat
    def set_asigurat(self, asigurat): self.asigurat = asigurat
    def add_asigurat(self, value): self.asigurat.append(value)
    def insert_asigurat(self, index, value): self.asigurat[index] = value
    def get_luna_r(self): return self.luna_r
    def set_luna_r(self, luna_r): self.luna_r = luna_r
    def get_d_rec(self): return self.d_rec
    def set_d_rec(self, d_rec): self.d_rec = d_rec
    def get_an_r(self): return self.an_r
    def set_an_r(self, an_r): self.an_r = an_r
    def get_nume_declar(self): return self.nume_declar
    def set_nume_declar(self, nume_declar): self.nume_declar = nume_declar
    def get_functie_declar(self): return self.functie_declar
    def set_functie_declar(self, functie_declar): self.functie_declar = functie_declar
    def get_prenume_declar(self): return self.prenume_declar
    def set_prenume_declar(self, prenume_declar): self.prenume_declar = prenume_declar
    def export(self, outfile, level, namespace_='', name_='declaratieUnica', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='declaratieUnica')
        if self.hasContent_():
            outfile.write('>\n')
            self.exportChildren(outfile, level + 1, namespace_, name_)
            showIndent(outfile, level)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='declaratieUnica'):
        outfile.write(' luna_r=%s' % (quote_attrib(self.luna_r), ))
        if self.d_rec is not None and 'd_rec' not in already_processed:
            already_processed.append('d_rec')
            outfile.write(' d_rec=%s' % (quote_attrib(self.d_rec), ))
        outfile.write(' an_r=%s' % (quote_attrib(self.an_r), ))
        outfile.write(' nume_declar=%s' % (self.gds_format_string(quote_attrib(self.nume_declar).encode(ExternalEncoding), input_name='nume_declar'), ))
        outfile.write(' functie_declar=%s' % (self.gds_format_string(quote_attrib(self.functie_declar).encode(ExternalEncoding), input_name='functie_declar'), ))
        outfile.write(' prenume_declar=%s' % (self.gds_format_string(quote_attrib(self.prenume_declar).encode(ExternalEncoding), input_name='prenume_declar'), ))
    def exportChildren(self, outfile, level, namespace_='', name_='declaratieUnica'):
        if self.angajator:
            self.angajator.export(outfile, level, namespace_, name_='angajator', )
        for asigurat_ in self.asigurat:
            asigurat_.export(outfile, level, namespace_, name_='asigurat')
    def hasContent_(self):
        if (
            self.angajator is not None or
            self.asigurat
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='declaratieUnica'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.luna_r is not None and 'luna_r' not in already_processed:
            already_processed.append('luna_r')
            showIndent(outfile, level)
            outfile.write('luna_r = %s,\n' % (self.luna_r,))
        if self.d_rec is not None and 'd_rec' not in already_processed:
            already_processed.append('d_rec')
            showIndent(outfile, level)
            outfile.write('d_rec = %s,\n' % (self.d_rec,))
        if self.an_r is not None and 'an_r' not in already_processed:
            already_processed.append('an_r')
            showIndent(outfile, level)
            outfile.write('an_r = %s,\n' % (self.an_r,))
        if self.nume_declar is not None and 'nume_declar' not in already_processed:
            already_processed.append('nume_declar')
            showIndent(outfile, level)
            outfile.write('nume_declar = "%s",\n' % (self.nume_declar,))
        if self.functie_declar is not None and 'functie_declar' not in already_processed:
            already_processed.append('functie_declar')
            showIndent(outfile, level)
            outfile.write('functie_declar = "%s",\n' % (self.functie_declar,))
        if self.prenume_declar is not None and 'prenume_declar' not in already_processed:
            already_processed.append('prenume_declar')
            showIndent(outfile, level)
            outfile.write('prenume_declar = "%s",\n' % (self.prenume_declar,))
    def exportLiteralChildren(self, outfile, level, name_):
        if self.angajator is not None:
            showIndent(outfile, level)
            outfile.write('angajator=model_.AngajatorType(\n')
            self.angajator.exportLiteral(outfile, level, name_='angajator')
            showIndent(outfile, level)
            outfile.write('),\n')
        showIndent(outfile, level)
        outfile.write('asigurat=[\n')
        level += 1
        for asigurat_ in self.asigurat:
            showIndent(outfile, level)
            outfile.write('model_.AsiguratType(\n')
            asigurat_.exportLiteral(outfile, level, name_='AsiguratType')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('luna_r')
        if value is not None and 'luna_r' not in already_processed:
            already_processed.append('luna_r')
            self.luna_r = value
        value = attrs.get('d_rec')
        if value is not None and 'd_rec' not in already_processed:
            already_processed.append('d_rec')
            self.d_rec = value
        value = attrs.get('an_r')
        if value is not None and 'an_r' not in already_processed:
            already_processed.append('an_r')
            self.an_r = value
        value = attrs.get('nume_declar')
        if value is not None and 'nume_declar' not in already_processed:
            already_processed.append('nume_declar')
            self.nume_declar = value
            self.nume_declar = ' '.join(self.nume_declar.split())
        value = attrs.get('functie_declar')
        if value is not None and 'functie_declar' not in already_processed:
            already_processed.append('functie_declar')
            self.functie_declar = value
            self.functie_declar = ' '.join(self.functie_declar.split())
        value = attrs.get('prenume_declar')
        if value is not None and 'prenume_declar' not in already_processed:
            already_processed.append('prenume_declar')
            self.prenume_declar = value
            self.prenume_declar = ' '.join(self.prenume_declar.split())
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        if nodeName_ == 'angajator': 
            obj_ = AngajatorType.factory()
            obj_.build(child_)
            self.set_angajator(obj_)
        elif nodeName_ == 'asigurat': 
            obj_ = AsiguratType.factory()
            obj_.build(child_)
            self.asigurat.append(obj_)
# end class declaratieUnica


class AngajatorType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, cif=None, faxFisc=None, tRisc=None, casaAng=None, telSoc=None, adrFisc=None, mailSoc=None, dat=None, adrSoc=None, rgCom=None, den=None, telFisc=None, faxSoc=None, totalPlata_A=None, mailFisc=None, caen=None, angajatorA=None, angajatorB=None, angajatorC1=None, angajatorC2=None, angajatorC3=None, angajatorC4=None, angajatorC5=None, angajatorC6=None, angajatorC7=None, angajatorD=None, angajatorE1=None, angajatorE2=None, angajatorE3=None, angajatorE4=None, angajatorF1=None, angajatorF2=None):
        self.cif = _cast(None, cif)
        self.faxFisc = _cast(None, faxFisc)
        self.tRisc = _cast(float, tRisc)
        self.casaAng = _cast(None, casaAng)
        self.telSoc = _cast(None, telSoc)
        self.adrFisc = _cast(None, adrFisc)
        self.mailSoc = _cast(None, mailSoc)
        self.dat = _cast(None, dat)
        self.adrSoc = _cast(None, adrSoc)
        self.rgCom = _cast(None, rgCom)
        self.den = _cast(None, den)
        self.telFisc = _cast(None, telFisc)
        self.faxSoc = _cast(None, faxSoc)
        self.totalPlata_A = _cast(None, totalPlata_A)
        self.mailFisc = _cast(None, mailFisc)
        self.caen = _cast(None, caen)
        if angajatorA is None:
            self.angajatorA = []
        else:
            self.angajatorA = angajatorA
        self.angajatorB = angajatorB
        self.angajatorC1 = angajatorC1
        self.angajatorC2 = angajatorC2
        self.angajatorC3 = angajatorC3
        self.angajatorC4 = angajatorC4
        if angajatorC5 is None:
            self.angajatorC5 = []
        else:
            self.angajatorC5 = angajatorC5
        self.angajatorC6 = angajatorC6
        self.angajatorC7 = angajatorC7
        self.angajatorD = angajatorD
        self.angajatorE1 = angajatorE1
        self.angajatorE2 = angajatorE2
        self.angajatorE3 = angajatorE3
        self.angajatorE4 = angajatorE4
        self.angajatorF1 = angajatorF1
        if angajatorF2 is None:
            self.angajatorF2 = []
        else:
            self.angajatorF2 = angajatorF2
    def factory(*args_, **kwargs_):
        if AngajatorType.subclass:
            return AngajatorType.subclass(*args_, **kwargs_)
        else:
            return AngajatorType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_angajatorA(self): return self.angajatorA
    def set_angajatorA(self, angajatorA): self.angajatorA = angajatorA
    def add_angajatorA(self, value): self.angajatorA.append(value)
    def insert_angajatorA(self, index, value): self.angajatorA[index] = value
    def get_angajatorB(self): return self.angajatorB
    def set_angajatorB(self, angajatorB): self.angajatorB = angajatorB
    def get_angajatorC1(self): return self.angajatorC1
    def set_angajatorC1(self, angajatorC1): self.angajatorC1 = angajatorC1
    def get_angajatorC2(self): return self.angajatorC2
    def set_angajatorC2(self, angajatorC2): self.angajatorC2 = angajatorC2
    def get_angajatorC3(self): return self.angajatorC3
    def set_angajatorC3(self, angajatorC3): self.angajatorC3 = angajatorC3
    def get_angajatorC4(self): return self.angajatorC4
    def set_angajatorC4(self, angajatorC4): self.angajatorC4 = angajatorC4
    def get_angajatorC5(self): return self.angajatorC5
    def set_angajatorC5(self, angajatorC5): self.angajatorC5 = angajatorC5
    def add_angajatorC5(self, value): self.angajatorC5.append(value)
    def insert_angajatorC5(self, index, value): self.angajatorC5[index] = value
    def get_angajatorC6(self): return self.angajatorC6
    def set_angajatorC6(self, angajatorC6): self.angajatorC6 = angajatorC6
    def get_angajatorC7(self): return self.angajatorC7
    def set_angajatorC7(self, angajatorC7): self.angajatorC7 = angajatorC7
    def get_angajatorD(self): return self.angajatorD
    def set_angajatorD(self, angajatorD): self.angajatorD = angajatorD
    def get_angajatorE1(self): return self.angajatorE1
    def set_angajatorE1(self, angajatorE1): self.angajatorE1 = angajatorE1
    def get_angajatorE2(self): return self.angajatorE2
    def set_angajatorE2(self, angajatorE2): self.angajatorE2 = angajatorE2
    def get_angajatorE3(self): return self.angajatorE3
    def set_angajatorE3(self, angajatorE3): self.angajatorE3 = angajatorE3
    def get_angajatorE4(self): return self.angajatorE4
    def set_angajatorE4(self, angajatorE4): self.angajatorE4 = angajatorE4
    def get_angajatorF1(self): return self.angajatorF1
    def set_angajatorF1(self, angajatorF1): self.angajatorF1 = angajatorF1
    def get_angajatorF2(self): return self.angajatorF2
    def set_angajatorF2(self, angajatorF2): self.angajatorF2 = angajatorF2
    def add_angajatorF2(self, value): self.angajatorF2.append(value)
    def insert_angajatorF2(self, index, value): self.angajatorF2[index] = value
    def get_cif(self): return self.cif
    def set_cif(self, cif): self.cif = cif
    def get_faxFisc(self): return self.faxFisc
    def set_faxFisc(self, faxFisc): self.faxFisc = faxFisc
    def get_tRisc(self): return self.tRisc
    def set_tRisc(self, tRisc): self.tRisc = tRisc
    def get_casaAng(self): return self.casaAng
    def set_casaAng(self, casaAng): self.casaAng = casaAng
    def get_telSoc(self): return self.telSoc
    def set_telSoc(self, telSoc): self.telSoc = telSoc
    def get_adrFisc(self): return self.adrFisc
    def set_adrFisc(self, adrFisc): self.adrFisc = adrFisc
    def get_mailSoc(self): return self.mailSoc
    def set_mailSoc(self, mailSoc): self.mailSoc = mailSoc
    def get_dat(self): return self.dat
    def set_dat(self, dat): self.dat = dat
    def get_adrSoc(self): return self.adrSoc
    def set_adrSoc(self, adrSoc): self.adrSoc = adrSoc
    def get_rgCom(self): return self.rgCom
    def set_rgCom(self, rgCom): self.rgCom = rgCom
    def get_den(self): return self.den
    def set_den(self, den): self.den = den
    def get_telFisc(self): return self.telFisc
    def set_telFisc(self, telFisc): self.telFisc = telFisc
    def get_faxSoc(self): return self.faxSoc
    def set_faxSoc(self, faxSoc): self.faxSoc = faxSoc
    def get_totalPlata_A(self): return self.totalPlata_A
    def set_totalPlata_A(self, totalPlata_A): self.totalPlata_A = totalPlata_A
    def get_mailFisc(self): return self.mailFisc
    def set_mailFisc(self, mailFisc): self.mailFisc = mailFisc
    def get_caen(self): return self.caen
    def set_caen(self, caen): self.caen = caen
    def export(self, outfile, level, namespace_='', name_='AngajatorType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorType')
        if self.hasContent_():
            outfile.write('>\n')
            self.exportChildren(outfile, level + 1, namespace_, name_)
            showIndent(outfile, level)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorType'):
        outfile.write(' cif=%s' % (quote_attrib(self.cif), ))
        if self.faxFisc is not None and 'faxFisc' not in already_processed:
            already_processed.append('faxFisc')
            outfile.write(' faxFisc=%s' % (quote_attrib(self.faxFisc), ))
        if self.tRisc is not None and 'tRisc' not in already_processed:
            already_processed.append('tRisc')
            outfile.write(' tRisc="%s"' % self.gds_format_string(self.tRisc, input_name='tRisc'))
        outfile.write(' casaAng=%s' % (quote_attrib(self.casaAng), ))
        if self.telSoc is not None and 'telSoc' not in already_processed:
            already_processed.append('telSoc')
            outfile.write(' telSoc=%s' % (quote_attrib(self.telSoc), ))
        if self.adrFisc is not None and 'adrFisc' not in already_processed:
            already_processed.append('adrFisc')
            outfile.write(' adrFisc=%s' % (self.gds_format_string(quote_attrib(self.adrFisc).encode(ExternalEncoding), input_name='adrFisc'), ))
        if self.mailSoc is not None and 'mailSoc' not in already_processed:
            already_processed.append('mailSoc')
            outfile.write(' mailSoc=%s' % (quote_attrib(self.mailSoc), ))
        if self.dat is not None and 'dat' not in already_processed:
            already_processed.append('dat')
            outfile.write(' dat=%s' % (quote_attrib(self.dat), ))
        if self.adrSoc is not None and 'adrSoc' not in already_processed:
            already_processed.append('adrSoc')
            outfile.write(' adrSoc=%s' % (self.gds_format_string(quote_attrib(self.adrSoc).encode(ExternalEncoding), input_name='adrSoc'), ))
        if self.rgCom is not None and 'rgCom' not in already_processed:
            already_processed.append('rgCom')
            outfile.write(' rgCom=%s' % (quote_attrib(self.rgCom), ))
        outfile.write(' den=%s' % (self.gds_format_string(quote_attrib(self.den).encode(ExternalEncoding), input_name='den'), ))
        if self.telFisc is not None and 'telFisc' not in already_processed:
            already_processed.append('telFisc')
            outfile.write(' telFisc=%s' % (quote_attrib(self.telFisc), ))
        if self.faxSoc is not None and 'faxSoc' not in already_processed:
            already_processed.append('faxSoc')
            outfile.write(' faxSoc=%s' % (quote_attrib(self.faxSoc), ))
        outfile.write(' totalPlata_A=%s' % (quote_attrib(self.totalPlata_A), ))
        if self.mailFisc is not None and 'mailFisc' not in already_processed:
            already_processed.append('mailFisc')
            outfile.write(' mailFisc=%s' % (quote_attrib(self.mailFisc), ))
        outfile.write(' caen=%s' % (quote_attrib(self.caen), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorType'):
        for angajatorA_ in self.angajatorA:
            angajatorA_.export(outfile, level, namespace_, name_='angajatorA')
        if self.angajatorB:
            self.angajatorB.export(outfile, level, namespace_, name_='angajatorB', )
        if self.angajatorC1:
            self.angajatorC1.export(outfile, level, namespace_, name_='angajatorC1')
        if self.angajatorC2:
            self.angajatorC2.export(outfile, level, namespace_, name_='angajatorC2')
        if self.angajatorC3:
            self.angajatorC3.export(outfile, level, namespace_, name_='angajatorC3')
        if self.angajatorC4:
            self.angajatorC4.export(outfile, level, namespace_, name_='angajatorC4')
        for angajatorC5_ in self.angajatorC5:
            angajatorC5_.export(outfile, level, namespace_, name_='angajatorC5')
        if self.angajatorC6:
            self.angajatorC6.export(outfile, level, namespace_, name_='angajatorC6', )
        if self.angajatorC7:
            self.angajatorC7.export(outfile, level, namespace_, name_='angajatorC7')
        if self.angajatorD:
            self.angajatorD.export(outfile, level, namespace_, name_='angajatorD')
        if self.angajatorE1:
            self.angajatorE1.export(outfile, level, namespace_, name_='angajatorE1')
        if self.angajatorE2:
            self.angajatorE2.export(outfile, level, namespace_, name_='angajatorE2')
        if self.angajatorE3:
            self.angajatorE3.export(outfile, level, namespace_, name_='angajatorE3')
        if self.angajatorE4:
            self.angajatorE4.export(outfile, level, namespace_, name_='angajatorE4')
        if self.angajatorF1:
            self.angajatorF1.export(outfile, level, namespace_, name_='angajatorF1', )
        for angajatorF2_ in self.angajatorF2:
            angajatorF2_.export(outfile, level, namespace_, name_='angajatorF2')
    def hasContent_(self):
        if (
            self.angajatorA or
            self.angajatorB is not None or
            self.angajatorC1 is not None or
            self.angajatorC2 is not None or
            self.angajatorC3 is not None or
            self.angajatorC4 is not None or
            self.angajatorC5 or
            self.angajatorC6 is not None or
            self.angajatorC7 is not None or
            self.angajatorD is not None or
            self.angajatorE1 is not None or
            self.angajatorE2 is not None or
            self.angajatorE3 is not None or
            self.angajatorE4 is not None or
            self.angajatorF1 is not None or
            self.angajatorF2
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.cif is not None and 'cif' not in already_processed:
            already_processed.append('cif')
            showIndent(outfile, level)
            outfile.write('cif = %s,\n' % (self.cif,))
        if self.faxFisc is not None and 'faxFisc' not in already_processed:
            already_processed.append('faxFisc')
            showIndent(outfile, level)
            outfile.write('faxFisc = %s,\n' % (self.faxFisc,))
        if self.tRisc is not None and 'tRisc' not in already_processed:
            already_processed.append('tRisc')
            showIndent(outfile, level)
            outfile.write('tRisc = %e,\n' % (self.tRisc,))
        if self.casaAng is not None and 'casaAng' not in already_processed:
            already_processed.append('casaAng')
            showIndent(outfile, level)
            outfile.write('casaAng = %s,\n' % (self.casaAng,))
        if self.telSoc is not None and 'telSoc' not in already_processed:
            already_processed.append('telSoc')
            showIndent(outfile, level)
            outfile.write('telSoc = %s,\n' % (self.telSoc,))
        if self.adrFisc is not None and 'adrFisc' not in already_processed:
            already_processed.append('adrFisc')
            showIndent(outfile, level)
            outfile.write('adrFisc = "%s",\n' % (self.adrFisc,))
        if self.mailSoc is not None and 'mailSoc' not in already_processed:
            already_processed.append('mailSoc')
            showIndent(outfile, level)
            outfile.write('mailSoc = %s,\n' % (self.mailSoc,))
        if self.dat is not None and 'dat' not in already_processed:
            already_processed.append('dat')
            showIndent(outfile, level)
            outfile.write('dat = %s,\n' % (self.dat,))
        if self.adrSoc is not None and 'adrSoc' not in already_processed:
            already_processed.append('adrSoc')
            showIndent(outfile, level)
            outfile.write('adrSoc = "%s",\n' % (self.adrSoc,))
        if self.rgCom is not None and 'rgCom' not in already_processed:
            already_processed.append('rgCom')
            showIndent(outfile, level)
            outfile.write('rgCom = %s,\n' % (self.rgCom,))
        if self.den is not None and 'den' not in already_processed:
            already_processed.append('den')
            showIndent(outfile, level)
            outfile.write('den = "%s",\n' % (self.den,))
        if self.telFisc is not None and 'telFisc' not in already_processed:
            already_processed.append('telFisc')
            showIndent(outfile, level)
            outfile.write('telFisc = %s,\n' % (self.telFisc,))
        if self.faxSoc is not None and 'faxSoc' not in already_processed:
            already_processed.append('faxSoc')
            showIndent(outfile, level)
            outfile.write('faxSoc = %s,\n' % (self.faxSoc,))
        if self.totalPlata_A is not None and 'totalPlata_A' not in already_processed:
            already_processed.append('totalPlata_A')
            showIndent(outfile, level)
            outfile.write('totalPlata_A = %s,\n' % (self.totalPlata_A,))
        if self.mailFisc is not None and 'mailFisc' not in already_processed:
            already_processed.append('mailFisc')
            showIndent(outfile, level)
            outfile.write('mailFisc = %s,\n' % (self.mailFisc,))
        if self.caen is not None and 'caen' not in already_processed:
            already_processed.append('caen')
            showIndent(outfile, level)
            outfile.write('caen = %s,\n' % (self.caen,))
    def exportLiteralChildren(self, outfile, level, name_):
        showIndent(outfile, level)
        outfile.write('angajatorA=[\n')
        level += 1
        for angajatorA_ in self.angajatorA:
            showIndent(outfile, level)
            outfile.write('model_.AngajatorAType(\n')
            angajatorA_.exportLiteral(outfile, level, name_='AngajatorAType')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
        if self.angajatorB is not None:
            showIndent(outfile, level)
            outfile.write('angajatorB=model_.AngajatorBType(\n')
            self.angajatorB.exportLiteral(outfile, level, name_='angajatorB')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorC1 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC1=model_.AngajatorC1Type(\n')
            self.angajatorC1.exportLiteral(outfile, level, name_='angajatorC1')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorC2 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC2=model_.AngajatorC2Type(\n')
            self.angajatorC2.exportLiteral(outfile, level, name_='angajatorC2')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorC3 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC3=model_.AngajatorC3Type(\n')
            self.angajatorC3.exportLiteral(outfile, level, name_='angajatorC3')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorC4 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC4=model_.AngajatorC4Type(\n')
            self.angajatorC4.exportLiteral(outfile, level, name_='angajatorC4')
            showIndent(outfile, level)
            outfile.write('),\n')
        showIndent(outfile, level)
        outfile.write('angajatorC5=[\n')
        level += 1
        for angajatorC5_ in self.angajatorC5:
            showIndent(outfile, level)
            outfile.write('model_.AngajatorC5Type(\n')
            angajatorC5_.exportLiteral(outfile, level, name_='AngajatorC5Type')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
        if self.angajatorC6 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC6=model_.AngajatorC6Type(\n')
            self.angajatorC6.exportLiteral(outfile, level, name_='angajatorC6')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorC7 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorC7=model_.AngajatorC7Type(\n')
            self.angajatorC7.exportLiteral(outfile, level, name_='angajatorC7')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorD is not None:
            showIndent(outfile, level)
            outfile.write('angajatorD=model_.AngajatorDType(\n')
            self.angajatorD.exportLiteral(outfile, level, name_='angajatorD')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorE1 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorE1=model_.AngajatorE1Type(\n')
            self.angajatorE1.exportLiteral(outfile, level, name_='angajatorE1')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorE2 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorE2=model_.AngajatorE2Type(\n')
            self.angajatorE2.exportLiteral(outfile, level, name_='angajatorE2')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorE3 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorE3=model_.AngajatorE3Type(\n')
            self.angajatorE3.exportLiteral(outfile, level, name_='angajatorE3')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorE4 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorE4=model_.AngajatorE4Type(\n')
            self.angajatorE4.exportLiteral(outfile, level, name_='angajatorE4')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.angajatorF1 is not None:
            showIndent(outfile, level)
            outfile.write('angajatorF1=model_.AngajatorF1Type(\n')
            self.angajatorF1.exportLiteral(outfile, level, name_='angajatorF1')
            showIndent(outfile, level)
            outfile.write('),\n')
        showIndent(outfile, level)
        outfile.write('angajatorF2=[\n')
        level += 1
        for angajatorF2_ in self.angajatorF2:
            showIndent(outfile, level)
            outfile.write('model_.AngajatorF2Type(\n')
            angajatorF2_.exportLiteral(outfile, level, name_='AngajatorF2Type')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('cif')
        if value is not None and 'cif' not in already_processed:
            already_processed.append('cif')
            self.cif = value
        value = attrs.get('faxFisc')
        if value is not None and 'faxFisc' not in already_processed:
            already_processed.append('faxFisc')
            self.faxFisc = value
        value = attrs.get('tRisc')
        if value is not None and 'tRisc' not in already_processed:
            already_processed.append('tRisc')
            try:
                self.tRisc = float(value)
            except ValueError, exp:
                raise ValueError('Bad float/double attribute (tRisc): %s' % exp)
        value = attrs.get('casaAng')
        if value is not None and 'casaAng' not in already_processed:
            already_processed.append('casaAng')
            self.casaAng = value
        value = attrs.get('telSoc')
        if value is not None and 'telSoc' not in already_processed:
            already_processed.append('telSoc')
            self.telSoc = value
        value = attrs.get('adrFisc')
        if value is not None and 'adrFisc' not in already_processed:
            already_processed.append('adrFisc')
            self.adrFisc = value
            self.adrFisc = ' '.join(self.adrFisc.split())
        value = attrs.get('mailSoc')
        if value is not None and 'mailSoc' not in already_processed:
            already_processed.append('mailSoc')
            self.mailSoc = value
        value = attrs.get('dat')
        if value is not None and 'dat' not in already_processed:
            already_processed.append('dat')
            self.dat = value
        value = attrs.get('adrSoc')
        if value is not None and 'adrSoc' not in already_processed:
            already_processed.append('adrSoc')
            self.adrSoc = value
            self.adrSoc = ' '.join(self.adrSoc.split())
        value = attrs.get('rgCom')
        if value is not None and 'rgCom' not in already_processed:
            already_processed.append('rgCom')
            self.rgCom = value
        value = attrs.get('den')
        if value is not None and 'den' not in already_processed:
            already_processed.append('den')
            self.den = value
            self.den = ' '.join(self.den.split())
        value = attrs.get('telFisc')
        if value is not None and 'telFisc' not in already_processed:
            already_processed.append('telFisc')
            self.telFisc = value
        value = attrs.get('faxSoc')
        if value is not None and 'faxSoc' not in already_processed:
            already_processed.append('faxSoc')
            self.faxSoc = value
        value = attrs.get('totalPlata_A')
        if value is not None and 'totalPlata_A' not in already_processed:
            already_processed.append('totalPlata_A')
            self.totalPlata_A = value
        value = attrs.get('mailFisc')
        if value is not None and 'mailFisc' not in already_processed:
            already_processed.append('mailFisc')
            self.mailFisc = value
        value = attrs.get('caen')
        if value is not None and 'caen' not in already_processed:
            already_processed.append('caen')
            self.caen = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        if nodeName_ == 'angajatorA': 
            obj_ = AngajatorAType.factory()
            obj_.build(child_)
            self.angajatorA.append(obj_)
        elif nodeName_ == 'angajatorB': 
            obj_ = AngajatorBType.factory()
            obj_.build(child_)
            self.set_angajatorB(obj_)
        elif nodeName_ == 'angajatorC1': 
            obj_ = AngajatorC1Type.factory()
            obj_.build(child_)
            self.set_angajatorC1(obj_)
        elif nodeName_ == 'angajatorC2': 
            obj_ = AngajatorC2Type.factory()
            obj_.build(child_)
            self.set_angajatorC2(obj_)
        elif nodeName_ == 'angajatorC3': 
            obj_ = AngajatorC3Type.factory()
            obj_.build(child_)
            self.set_angajatorC3(obj_)
        elif nodeName_ == 'angajatorC4': 
            obj_ = AngajatorC4Type.factory()
            obj_.build(child_)
            self.set_angajatorC4(obj_)
        elif nodeName_ == 'angajatorC5': 
            obj_ = AngajatorC5Type.factory()
            obj_.build(child_)
            self.angajatorC5.append(obj_)
        elif nodeName_ == 'angajatorC6': 
            obj_ = AngajatorC6Type.factory()
            obj_.build(child_)
            self.set_angajatorC6(obj_)
        elif nodeName_ == 'angajatorC7': 
            obj_ = AngajatorC7Type.factory()
            obj_.build(child_)
            self.set_angajatorC7(obj_)
        elif nodeName_ == 'angajatorD': 
            obj_ = AngajatorDType.factory()
            obj_.build(child_)
            self.set_angajatorD(obj_)
        elif nodeName_ == 'angajatorE1': 
            obj_ = AngajatorE1Type.factory()
            obj_.build(child_)
            self.set_angajatorE1(obj_)
        elif nodeName_ == 'angajatorE2': 
            obj_ = AngajatorE2Type.factory()
            obj_.build(child_)
            self.set_angajatorE2(obj_)
        elif nodeName_ == 'angajatorE3': 
            obj_ = AngajatorE3Type.factory()
            obj_.build(child_)
            self.set_angajatorE3(obj_)
        elif nodeName_ == 'angajatorE4': 
            obj_ = AngajatorE4Type.factory()
            obj_.build(child_)
            self.set_angajatorE4(obj_)
        elif nodeName_ == 'angajatorF1': 
            obj_ = AngajatorF1Type.factory()
            obj_.build(child_)
            self.set_angajatorF1(obj_)
        elif nodeName_ == 'angajatorF2': 
            obj_ = AngajatorF2Type.factory()
            obj_.build(child_)
            self.angajatorF2.append(obj_)
# end class AngajatorType


class AngajatorAType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, A_codOblig=None, A_codBugetar=None, A_plata=None, A_datorat=None, A_deductibil=None, valueOf_=None):
        self.A_codOblig = _cast(None, A_codOblig)
        self.A_codBugetar = _cast(None, A_codBugetar)
        self.A_plata = _cast(None, A_plata)
        self.A_datorat = _cast(None, A_datorat)
        self.A_deductibil = _cast(None, A_deductibil)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorAType.subclass:
            return AngajatorAType.subclass(*args_, **kwargs_)
        else:
            return AngajatorAType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_A_codOblig(self): return self.A_codOblig
    def set_A_codOblig(self, A_codOblig): self.A_codOblig = A_codOblig
    def get_A_codBugetar(self): return self.A_codBugetar
    def set_A_codBugetar(self, A_codBugetar): self.A_codBugetar = A_codBugetar
    def get_A_plata(self): return self.A_plata
    def set_A_plata(self, A_plata): self.A_plata = A_plata
    def get_A_datorat(self): return self.A_datorat
    def set_A_datorat(self, A_datorat): self.A_datorat = A_datorat
    def get_A_deductibil(self): return self.A_deductibil
    def set_A_deductibil(self, A_deductibil): self.A_deductibil = A_deductibil
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorAType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorAType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorAType'):
        outfile.write(' A_codOblig=%s' % (quote_attrib(self.A_codOblig), ))
        outfile.write(' A_codBugetar=%s' % (quote_attrib(self.A_codBugetar), ))
        outfile.write(' A_plata=%s' % (quote_attrib(self.A_plata), ))
        outfile.write(' A_datorat=%s' % (quote_attrib(self.A_datorat), ))
        if self.A_deductibil is not None and 'A_deductibil' not in already_processed:
            already_processed.append('A_deductibil')
            outfile.write(' A_deductibil=%s' % (quote_attrib(self.A_deductibil), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorAType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorAType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.A_codOblig is not None and 'A_codOblig' not in already_processed:
            already_processed.append('A_codOblig')
            showIndent(outfile, level)
            outfile.write('A_codOblig = %s,\n' % (self.A_codOblig,))
        if self.A_codBugetar is not None and 'A_codBugetar' not in already_processed:
            already_processed.append('A_codBugetar')
            showIndent(outfile, level)
            outfile.write('A_codBugetar = %s,\n' % (self.A_codBugetar,))
        if self.A_plata is not None and 'A_plata' not in already_processed:
            already_processed.append('A_plata')
            showIndent(outfile, level)
            outfile.write('A_plata = %s,\n' % (self.A_plata,))
        if self.A_datorat is not None and 'A_datorat' not in already_processed:
            already_processed.append('A_datorat')
            showIndent(outfile, level)
            outfile.write('A_datorat = %s,\n' % (self.A_datorat,))
        if self.A_deductibil is not None and 'A_deductibil' not in already_processed:
            already_processed.append('A_deductibil')
            showIndent(outfile, level)
            outfile.write('A_deductibil = %s,\n' % (self.A_deductibil,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('A_codOblig')
        if value is not None and 'A_codOblig' not in already_processed:
            already_processed.append('A_codOblig')
            self.A_codOblig = value
        value = attrs.get('A_codBugetar')
        if value is not None and 'A_codBugetar' not in already_processed:
            already_processed.append('A_codBugetar')
            self.A_codBugetar = value
        value = attrs.get('A_plata')
        if value is not None and 'A_plata' not in already_processed:
            already_processed.append('A_plata')
            self.A_plata = value
        value = attrs.get('A_datorat')
        if value is not None and 'A_datorat' not in already_processed:
            already_processed.append('A_datorat')
            self.A_datorat = value
        value = attrs.get('A_deductibil')
        if value is not None and 'A_deductibil' not in already_processed:
            already_processed.append('A_deductibil')
            self.A_deductibil = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorAType


class AngajatorBType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B_sanatate=None, B_brutSalarii=None, B_pensie=None, B_cnp=None, valueOf_=None):
        self.B_sanatate = _cast(None, B_sanatate)
        self.B_brutSalarii = _cast(None, B_brutSalarii)
        self.B_pensie = _cast(None, B_pensie)
        self.B_cnp = _cast(None, B_cnp)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorBType.subclass:
            return AngajatorBType.subclass(*args_, **kwargs_)
        else:
            return AngajatorBType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_B_sanatate(self): return self.B_sanatate
    def set_B_sanatate(self, B_sanatate): self.B_sanatate = B_sanatate
    def get_B_brutSalarii(self): return self.B_brutSalarii
    def set_B_brutSalarii(self, B_brutSalarii): self.B_brutSalarii = B_brutSalarii
    def get_B_pensie(self): return self.B_pensie
    def set_B_pensie(self, B_pensie): self.B_pensie = B_pensie
    def get_B_cnp(self): return self.B_cnp
    def set_B_cnp(self, B_cnp): self.B_cnp = B_cnp
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorBType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorBType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorBType'):
        outfile.write(' B_sanatate=%s' % (quote_attrib(self.B_sanatate), ))
        outfile.write(' B_brutSalarii=%s' % (quote_attrib(self.B_brutSalarii), ))
        outfile.write(' B_pensie=%s' % (quote_attrib(self.B_pensie), ))
        outfile.write(' B_cnp=%s' % (quote_attrib(self.B_cnp), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorBType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorBType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B_sanatate is not None and 'B_sanatate' not in already_processed:
            already_processed.append('B_sanatate')
            showIndent(outfile, level)
            outfile.write('B_sanatate = %s,\n' % (self.B_sanatate,))
        if self.B_brutSalarii is not None and 'B_brutSalarii' not in already_processed:
            already_processed.append('B_brutSalarii')
            showIndent(outfile, level)
            outfile.write('B_brutSalarii = %s,\n' % (self.B_brutSalarii,))
        if self.B_pensie is not None and 'B_pensie' not in already_processed:
            already_processed.append('B_pensie')
            showIndent(outfile, level)
            outfile.write('B_pensie = %s,\n' % (self.B_pensie,))
        if self.B_cnp is not None and 'B_cnp' not in already_processed:
            already_processed.append('B_cnp')
            showIndent(outfile, level)
            outfile.write('B_cnp = %s,\n' % (self.B_cnp,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B_sanatate')
        if value is not None and 'B_sanatate' not in already_processed:
            already_processed.append('B_sanatate')
            self.B_sanatate = value
        value = attrs.get('B_brutSalarii')
        if value is not None and 'B_brutSalarii' not in already_processed:
            already_processed.append('B_brutSalarii')
            self.B_brutSalarii = value
        value = attrs.get('B_pensie')
        if value is not None and 'B_pensie' not in already_processed:
            already_processed.append('B_pensie')
            self.B_pensie = value
        value = attrs.get('B_cnp')
        if value is not None and 'B_cnp' not in already_processed:
            already_processed.append('B_cnp')
            self.B_cnp = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorBType


class AngajatorC1Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C1_T2=None, C1_T3=None, C1_7=None, C1_T1=None, C1_11=None, C1_13=None, C1_12=None, C1_21=None, C1_22=None, C1_23=None, C1_33=None, C1_32=None, C1_31=None, C1_6=None, C1_5=None, C1_T=None, valueOf_=None):
        self.C1_T2 = _cast(None, C1_T2)
        self.C1_T3 = _cast(None, C1_T3)
        self.C1_7 = _cast(None, C1_7)
        self.C1_T1 = _cast(None, C1_T1)
        self.C1_11 = _cast(None, C1_11)
        self.C1_13 = _cast(None, C1_13)
        self.C1_12 = _cast(None, C1_12)
        self.C1_21 = _cast(None, C1_21)
        self.C1_22 = _cast(None, C1_22)
        self.C1_23 = _cast(None, C1_23)
        self.C1_33 = _cast(None, C1_33)
        self.C1_32 = _cast(None, C1_32)
        self.C1_31 = _cast(None, C1_31)
        self.C1_6 = _cast(None, C1_6)
        self.C1_5 = _cast(None, C1_5)
        self.C1_T = _cast(None, C1_T)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC1Type.subclass:
            return AngajatorC1Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC1Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C1_T2(self): return self.C1_T2
    def set_C1_T2(self, C1_T2): self.C1_T2 = C1_T2
    def get_C1_T3(self): return self.C1_T3
    def set_C1_T3(self, C1_T3): self.C1_T3 = C1_T3
    def get_C1_7(self): return self.C1_7
    def set_C1_7(self, C1_7): self.C1_7 = C1_7
    def get_C1_T1(self): return self.C1_T1
    def set_C1_T1(self, C1_T1): self.C1_T1 = C1_T1
    def get_C1_11(self): return self.C1_11
    def set_C1_11(self, C1_11): self.C1_11 = C1_11
    def get_C1_13(self): return self.C1_13
    def set_C1_13(self, C1_13): self.C1_13 = C1_13
    def get_C1_12(self): return self.C1_12
    def set_C1_12(self, C1_12): self.C1_12 = C1_12
    def get_C1_21(self): return self.C1_21
    def set_C1_21(self, C1_21): self.C1_21 = C1_21
    def get_C1_22(self): return self.C1_22
    def set_C1_22(self, C1_22): self.C1_22 = C1_22
    def get_C1_23(self): return self.C1_23
    def set_C1_23(self, C1_23): self.C1_23 = C1_23
    def get_C1_33(self): return self.C1_33
    def set_C1_33(self, C1_33): self.C1_33 = C1_33
    def get_C1_32(self): return self.C1_32
    def set_C1_32(self, C1_32): self.C1_32 = C1_32
    def get_C1_31(self): return self.C1_31
    def set_C1_31(self, C1_31): self.C1_31 = C1_31
    def get_C1_6(self): return self.C1_6
    def set_C1_6(self, C1_6): self.C1_6 = C1_6
    def get_C1_5(self): return self.C1_5
    def set_C1_5(self, C1_5): self.C1_5 = C1_5
    def get_C1_T(self): return self.C1_T
    def set_C1_T(self, C1_T): self.C1_T = C1_T
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC1Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC1Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC1Type'):
        if self.C1_T2 is not None and 'C1_T2' not in already_processed:
            already_processed.append('C1_T2')
            outfile.write(' C1_T2=%s' % (quote_attrib(self.C1_T2), ))
        if self.C1_T3 is not None and 'C1_T3' not in already_processed:
            already_processed.append('C1_T3')
            outfile.write(' C1_T3=%s' % (quote_attrib(self.C1_T3), ))
        if self.C1_7 is not None and 'C1_7' not in already_processed:
            already_processed.append('C1_7')
            outfile.write(' C1_7=%s' % (quote_attrib(self.C1_7), ))
        if self.C1_T1 is not None and 'C1_T1' not in already_processed:
            already_processed.append('C1_T1')
            outfile.write(' C1_T1=%s' % (quote_attrib(self.C1_T1), ))
        if self.C1_11 is not None and 'C1_11' not in already_processed:
            already_processed.append('C1_11')
            outfile.write(' C1_11=%s' % (quote_attrib(self.C1_11), ))
        if self.C1_13 is not None and 'C1_13' not in already_processed:
            already_processed.append('C1_13')
            outfile.write(' C1_13=%s' % (quote_attrib(self.C1_13), ))
        if self.C1_12 is not None and 'C1_12' not in already_processed:
            already_processed.append('C1_12')
            outfile.write(' C1_12=%s' % (quote_attrib(self.C1_12), ))
        if self.C1_21 is not None and 'C1_21' not in already_processed:
            already_processed.append('C1_21')
            outfile.write(' C1_21=%s' % (quote_attrib(self.C1_21), ))
        if self.C1_22 is not None and 'C1_22' not in already_processed:
            already_processed.append('C1_22')
            outfile.write(' C1_22=%s' % (quote_attrib(self.C1_22), ))
        if self.C1_23 is not None and 'C1_23' not in already_processed:
            already_processed.append('C1_23')
            outfile.write(' C1_23=%s' % (quote_attrib(self.C1_23), ))
        if self.C1_33 is not None and 'C1_33' not in already_processed:
            already_processed.append('C1_33')
            outfile.write(' C1_33=%s' % (quote_attrib(self.C1_33), ))
        if self.C1_32 is not None and 'C1_32' not in already_processed:
            already_processed.append('C1_32')
            outfile.write(' C1_32=%s' % (quote_attrib(self.C1_32), ))
        if self.C1_31 is not None and 'C1_31' not in already_processed:
            already_processed.append('C1_31')
            outfile.write(' C1_31=%s' % (quote_attrib(self.C1_31), ))
        if self.C1_6 is not None and 'C1_6' not in already_processed:
            already_processed.append('C1_6')
            outfile.write(' C1_6=%s' % (quote_attrib(self.C1_6), ))
        if self.C1_5 is not None and 'C1_5' not in already_processed:
            already_processed.append('C1_5')
            outfile.write(' C1_5=%s' % (quote_attrib(self.C1_5), ))
        if self.C1_T is not None and 'C1_T' not in already_processed:
            already_processed.append('C1_T')
            outfile.write(' C1_T=%s' % (quote_attrib(self.C1_T), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC1Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC1Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C1_T2 is not None and 'C1_T2' not in already_processed:
            already_processed.append('C1_T2')
            showIndent(outfile, level)
            outfile.write('C1_T2 = %s,\n' % (self.C1_T2,))
        if self.C1_T3 is not None and 'C1_T3' not in already_processed:
            already_processed.append('C1_T3')
            showIndent(outfile, level)
            outfile.write('C1_T3 = %s,\n' % (self.C1_T3,))
        if self.C1_7 is not None and 'C1_7' not in already_processed:
            already_processed.append('C1_7')
            showIndent(outfile, level)
            outfile.write('C1_7 = %s,\n' % (self.C1_7,))
        if self.C1_T1 is not None and 'C1_T1' not in already_processed:
            already_processed.append('C1_T1')
            showIndent(outfile, level)
            outfile.write('C1_T1 = %s,\n' % (self.C1_T1,))
        if self.C1_11 is not None and 'C1_11' not in already_processed:
            already_processed.append('C1_11')
            showIndent(outfile, level)
            outfile.write('C1_11 = %s,\n' % (self.C1_11,))
        if self.C1_13 is not None and 'C1_13' not in already_processed:
            already_processed.append('C1_13')
            showIndent(outfile, level)
            outfile.write('C1_13 = %s,\n' % (self.C1_13,))
        if self.C1_12 is not None and 'C1_12' not in already_processed:
            already_processed.append('C1_12')
            showIndent(outfile, level)
            outfile.write('C1_12 = %s,\n' % (self.C1_12,))
        if self.C1_21 is not None and 'C1_21' not in already_processed:
            already_processed.append('C1_21')
            showIndent(outfile, level)
            outfile.write('C1_21 = %s,\n' % (self.C1_21,))
        if self.C1_22 is not None and 'C1_22' not in already_processed:
            already_processed.append('C1_22')
            showIndent(outfile, level)
            outfile.write('C1_22 = %s,\n' % (self.C1_22,))
        if self.C1_23 is not None and 'C1_23' not in already_processed:
            already_processed.append('C1_23')
            showIndent(outfile, level)
            outfile.write('C1_23 = %s,\n' % (self.C1_23,))
        if self.C1_33 is not None and 'C1_33' not in already_processed:
            already_processed.append('C1_33')
            showIndent(outfile, level)
            outfile.write('C1_33 = %s,\n' % (self.C1_33,))
        if self.C1_32 is not None and 'C1_32' not in already_processed:
            already_processed.append('C1_32')
            showIndent(outfile, level)
            outfile.write('C1_32 = %s,\n' % (self.C1_32,))
        if self.C1_31 is not None and 'C1_31' not in already_processed:
            already_processed.append('C1_31')
            showIndent(outfile, level)
            outfile.write('C1_31 = %s,\n' % (self.C1_31,))
        if self.C1_6 is not None and 'C1_6' not in already_processed:
            already_processed.append('C1_6')
            showIndent(outfile, level)
            outfile.write('C1_6 = %s,\n' % (self.C1_6,))
        if self.C1_5 is not None and 'C1_5' not in already_processed:
            already_processed.append('C1_5')
            showIndent(outfile, level)
            outfile.write('C1_5 = %s,\n' % (self.C1_5,))
        if self.C1_T is not None and 'C1_T' not in already_processed:
            already_processed.append('C1_T')
            showIndent(outfile, level)
            outfile.write('C1_T = %s,\n' % (self.C1_T,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C1_T2')
        if value is not None and 'C1_T2' not in already_processed:
            already_processed.append('C1_T2')
            self.C1_T2 = value
        value = attrs.get('C1_T3')
        if value is not None and 'C1_T3' not in already_processed:
            already_processed.append('C1_T3')
            self.C1_T3 = value
        value = attrs.get('C1_7')
        if value is not None and 'C1_7' not in already_processed:
            already_processed.append('C1_7')
            self.C1_7 = value
        value = attrs.get('C1_T1')
        if value is not None and 'C1_T1' not in already_processed:
            already_processed.append('C1_T1')
            self.C1_T1 = value
        value = attrs.get('C1_11')
        if value is not None and 'C1_11' not in already_processed:
            already_processed.append('C1_11')
            self.C1_11 = value
        value = attrs.get('C1_13')
        if value is not None and 'C1_13' not in already_processed:
            already_processed.append('C1_13')
            self.C1_13 = value
        value = attrs.get('C1_12')
        if value is not None and 'C1_12' not in already_processed:
            already_processed.append('C1_12')
            self.C1_12 = value
        value = attrs.get('C1_21')
        if value is not None and 'C1_21' not in already_processed:
            already_processed.append('C1_21')
            self.C1_21 = value
        value = attrs.get('C1_22')
        if value is not None and 'C1_22' not in already_processed:
            already_processed.append('C1_22')
            self.C1_22 = value
        value = attrs.get('C1_23')
        if value is not None and 'C1_23' not in already_processed:
            already_processed.append('C1_23')
            self.C1_23 = value
        value = attrs.get('C1_33')
        if value is not None and 'C1_33' not in already_processed:
            already_processed.append('C1_33')
            self.C1_33 = value
        value = attrs.get('C1_32')
        if value is not None and 'C1_32' not in already_processed:
            already_processed.append('C1_32')
            self.C1_32 = value
        value = attrs.get('C1_31')
        if value is not None and 'C1_31' not in already_processed:
            already_processed.append('C1_31')
            self.C1_31 = value
        value = attrs.get('C1_6')
        if value is not None and 'C1_6' not in already_processed:
            already_processed.append('C1_6')
            self.C1_6 = value
        value = attrs.get('C1_5')
        if value is not None and 'C1_5' not in already_processed:
            already_processed.append('C1_5')
            self.C1_5 = value
        value = attrs.get('C1_T')
        if value is not None and 'C1_T' not in already_processed:
            already_processed.append('C1_T')
            self.C1_T = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC1Type


class AngajatorC2Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C2_46=None, C2_44=None, C2_42=None, C2_41=None, C2_24=None, C2_26=None, C2_21=None, C2_22=None, C2_T6=None, C2_8=None, C2_9=None, C2_7=None, C2_120=None, C2_14=None, C2_15=None, C2_16=None, C2_10=None, C2_11=None, C2_12=None, C2_13=None, C2_51=None, C2_52=None, C2_54=None, C2_56=None, C2_36=None, C2_34=None, C2_32=None, C2_31=None, C2_130=None, C2_110=None, valueOf_=None):
        self.C2_46 = _cast(None, C2_46)
        self.C2_44 = _cast(None, C2_44)
        self.C2_42 = _cast(None, C2_42)
        self.C2_41 = _cast(None, C2_41)
        self.C2_24 = _cast(None, C2_24)
        self.C2_26 = _cast(None, C2_26)
        self.C2_21 = _cast(None, C2_21)
        self.C2_22 = _cast(None, C2_22)
        self.C2_T6 = _cast(None, C2_T6)
        self.C2_8 = _cast(None, C2_8)
        self.C2_9 = _cast(None, C2_9)
        self.C2_7 = _cast(None, C2_7)
        self.C2_120 = _cast(None, C2_120)
        self.C2_14 = _cast(None, C2_14)
        self.C2_15 = _cast(None, C2_15)
        self.C2_16 = _cast(None, C2_16)
        self.C2_10 = _cast(None, C2_10)
        self.C2_11 = _cast(None, C2_11)
        self.C2_12 = _cast(None, C2_12)
        self.C2_13 = _cast(None, C2_13)
        self.C2_51 = _cast(None, C2_51)
        self.C2_52 = _cast(None, C2_52)
        self.C2_54 = _cast(None, C2_54)
        self.C2_56 = _cast(None, C2_56)
        self.C2_36 = _cast(None, C2_36)
        self.C2_34 = _cast(None, C2_34)
        self.C2_32 = _cast(None, C2_32)
        self.C2_31 = _cast(None, C2_31)
        self.C2_130 = _cast(None, C2_130)
        self.C2_110 = _cast(None, C2_110)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC2Type.subclass:
            return AngajatorC2Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC2Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C2_46(self): return self.C2_46
    def set_C2_46(self, C2_46): self.C2_46 = C2_46
    def get_C2_44(self): return self.C2_44
    def set_C2_44(self, C2_44): self.C2_44 = C2_44
    def get_C2_42(self): return self.C2_42
    def set_C2_42(self, C2_42): self.C2_42 = C2_42
    def get_C2_41(self): return self.C2_41
    def set_C2_41(self, C2_41): self.C2_41 = C2_41
    def get_C2_24(self): return self.C2_24
    def set_C2_24(self, C2_24): self.C2_24 = C2_24
    def get_C2_26(self): return self.C2_26
    def set_C2_26(self, C2_26): self.C2_26 = C2_26
    def get_C2_21(self): return self.C2_21
    def set_C2_21(self, C2_21): self.C2_21 = C2_21
    def get_C2_22(self): return self.C2_22
    def set_C2_22(self, C2_22): self.C2_22 = C2_22
    def get_C2_T6(self): return self.C2_T6
    def set_C2_T6(self, C2_T6): self.C2_T6 = C2_T6
    def get_C2_8(self): return self.C2_8
    def set_C2_8(self, C2_8): self.C2_8 = C2_8
    def get_C2_9(self): return self.C2_9
    def set_C2_9(self, C2_9): self.C2_9 = C2_9
    def get_C2_7(self): return self.C2_7
    def set_C2_7(self, C2_7): self.C2_7 = C2_7
    def get_C2_120(self): return self.C2_120
    def set_C2_120(self, C2_120): self.C2_120 = C2_120
    def get_C2_14(self): return self.C2_14
    def set_C2_14(self, C2_14): self.C2_14 = C2_14
    def get_C2_15(self): return self.C2_15
    def set_C2_15(self, C2_15): self.C2_15 = C2_15
    def get_C2_16(self): return self.C2_16
    def set_C2_16(self, C2_16): self.C2_16 = C2_16
    def get_C2_10(self): return self.C2_10
    def set_C2_10(self, C2_10): self.C2_10 = C2_10
    def get_C2_11(self): return self.C2_11
    def set_C2_11(self, C2_11): self.C2_11 = C2_11
    def get_C2_12(self): return self.C2_12
    def set_C2_12(self, C2_12): self.C2_12 = C2_12
    def get_C2_13(self): return self.C2_13
    def set_C2_13(self, C2_13): self.C2_13 = C2_13
    def get_C2_51(self): return self.C2_51
    def set_C2_51(self, C2_51): self.C2_51 = C2_51
    def get_C2_52(self): return self.C2_52
    def set_C2_52(self, C2_52): self.C2_52 = C2_52
    def get_C2_54(self): return self.C2_54
    def set_C2_54(self, C2_54): self.C2_54 = C2_54
    def get_C2_56(self): return self.C2_56
    def set_C2_56(self, C2_56): self.C2_56 = C2_56
    def get_C2_36(self): return self.C2_36
    def set_C2_36(self, C2_36): self.C2_36 = C2_36
    def get_C2_34(self): return self.C2_34
    def set_C2_34(self, C2_34): self.C2_34 = C2_34
    def get_C2_32(self): return self.C2_32
    def set_C2_32(self, C2_32): self.C2_32 = C2_32
    def get_C2_31(self): return self.C2_31
    def set_C2_31(self, C2_31): self.C2_31 = C2_31
    def get_C2_130(self): return self.C2_130
    def set_C2_130(self, C2_130): self.C2_130 = C2_130
    def get_C2_110(self): return self.C2_110
    def set_C2_110(self, C2_110): self.C2_110 = C2_110
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC2Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC2Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC2Type'):
        if self.C2_46 is not None and 'C2_46' not in already_processed:
            already_processed.append('C2_46')
            outfile.write(' C2_46=%s' % (quote_attrib(self.C2_46), ))
        if self.C2_44 is not None and 'C2_44' not in already_processed:
            already_processed.append('C2_44')
            outfile.write(' C2_44=%s' % (quote_attrib(self.C2_44), ))
        if self.C2_42 is not None and 'C2_42' not in already_processed:
            already_processed.append('C2_42')
            outfile.write(' C2_42=%s' % (quote_attrib(self.C2_42), ))
        if self.C2_41 is not None and 'C2_41' not in already_processed:
            already_processed.append('C2_41')
            outfile.write(' C2_41=%s' % (quote_attrib(self.C2_41), ))
        if self.C2_24 is not None and 'C2_24' not in already_processed:
            already_processed.append('C2_24')
            outfile.write(' C2_24=%s' % (quote_attrib(self.C2_24), ))
        if self.C2_26 is not None and 'C2_26' not in already_processed:
            already_processed.append('C2_26')
            outfile.write(' C2_26=%s' % (quote_attrib(self.C2_26), ))
        if self.C2_21 is not None and 'C2_21' not in already_processed:
            already_processed.append('C2_21')
            outfile.write(' C2_21=%s' % (quote_attrib(self.C2_21), ))
        if self.C2_22 is not None and 'C2_22' not in already_processed:
            already_processed.append('C2_22')
            outfile.write(' C2_22=%s' % (quote_attrib(self.C2_22), ))
        if self.C2_T6 is not None and 'C2_T6' not in already_processed:
            already_processed.append('C2_T6')
            outfile.write(' C2_T6=%s' % (quote_attrib(self.C2_T6), ))
        if self.C2_8 is not None and 'C2_8' not in already_processed:
            already_processed.append('C2_8')
            outfile.write(' C2_8=%s' % (quote_attrib(self.C2_8), ))
        if self.C2_9 is not None and 'C2_9' not in already_processed:
            already_processed.append('C2_9')
            outfile.write(' C2_9=%s' % (quote_attrib(self.C2_9), ))
        if self.C2_7 is not None and 'C2_7' not in already_processed:
            already_processed.append('C2_7')
            outfile.write(' C2_7=%s' % (quote_attrib(self.C2_7), ))
        if self.C2_120 is not None and 'C2_120' not in already_processed:
            already_processed.append('C2_120')
            outfile.write(' C2_120=%s' % (quote_attrib(self.C2_120), ))
        if self.C2_14 is not None and 'C2_14' not in already_processed:
            already_processed.append('C2_14')
            outfile.write(' C2_14=%s' % (quote_attrib(self.C2_14), ))
        if self.C2_15 is not None and 'C2_15' not in already_processed:
            already_processed.append('C2_15')
            outfile.write(' C2_15=%s' % (quote_attrib(self.C2_15), ))
        if self.C2_16 is not None and 'C2_16' not in already_processed:
            already_processed.append('C2_16')
            outfile.write(' C2_16=%s' % (quote_attrib(self.C2_16), ))
        if self.C2_10 is not None and 'C2_10' not in already_processed:
            already_processed.append('C2_10')
            outfile.write(' C2_10=%s' % (quote_attrib(self.C2_10), ))
        if self.C2_11 is not None and 'C2_11' not in already_processed:
            already_processed.append('C2_11')
            outfile.write(' C2_11=%s' % (quote_attrib(self.C2_11), ))
        if self.C2_12 is not None and 'C2_12' not in already_processed:
            already_processed.append('C2_12')
            outfile.write(' C2_12=%s' % (quote_attrib(self.C2_12), ))
        if self.C2_13 is not None and 'C2_13' not in already_processed:
            already_processed.append('C2_13')
            outfile.write(' C2_13=%s' % (quote_attrib(self.C2_13), ))
        if self.C2_51 is not None and 'C2_51' not in already_processed:
            already_processed.append('C2_51')
            outfile.write(' C2_51=%s' % (quote_attrib(self.C2_51), ))
        if self.C2_52 is not None and 'C2_52' not in already_processed:
            already_processed.append('C2_52')
            outfile.write(' C2_52=%s' % (quote_attrib(self.C2_52), ))
        if self.C2_54 is not None and 'C2_54' not in already_processed:
            already_processed.append('C2_54')
            outfile.write(' C2_54=%s' % (quote_attrib(self.C2_54), ))
        if self.C2_56 is not None and 'C2_56' not in already_processed:
            already_processed.append('C2_56')
            outfile.write(' C2_56=%s' % (quote_attrib(self.C2_56), ))
        if self.C2_36 is not None and 'C2_36' not in already_processed:
            already_processed.append('C2_36')
            outfile.write(' C2_36=%s' % (quote_attrib(self.C2_36), ))
        if self.C2_34 is not None and 'C2_34' not in already_processed:
            already_processed.append('C2_34')
            outfile.write(' C2_34=%s' % (quote_attrib(self.C2_34), ))
        if self.C2_32 is not None and 'C2_32' not in already_processed:
            already_processed.append('C2_32')
            outfile.write(' C2_32=%s' % (quote_attrib(self.C2_32), ))
        if self.C2_31 is not None and 'C2_31' not in already_processed:
            already_processed.append('C2_31')
            outfile.write(' C2_31=%s' % (quote_attrib(self.C2_31), ))
        if self.C2_130 is not None and 'C2_130' not in already_processed:
            already_processed.append('C2_130')
            outfile.write(' C2_130=%s' % (quote_attrib(self.C2_130), ))
        if self.C2_110 is not None and 'C2_110' not in already_processed:
            already_processed.append('C2_110')
            outfile.write(' C2_110=%s' % (quote_attrib(self.C2_110), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC2Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC2Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C2_46 is not None and 'C2_46' not in already_processed:
            already_processed.append('C2_46')
            showIndent(outfile, level)
            outfile.write('C2_46 = %s,\n' % (self.C2_46,))
        if self.C2_44 is not None and 'C2_44' not in already_processed:
            already_processed.append('C2_44')
            showIndent(outfile, level)
            outfile.write('C2_44 = %s,\n' % (self.C2_44,))
        if self.C2_42 is not None and 'C2_42' not in already_processed:
            already_processed.append('C2_42')
            showIndent(outfile, level)
            outfile.write('C2_42 = %s,\n' % (self.C2_42,))
        if self.C2_41 is not None and 'C2_41' not in already_processed:
            already_processed.append('C2_41')
            showIndent(outfile, level)
            outfile.write('C2_41 = %s,\n' % (self.C2_41,))
        if self.C2_24 is not None and 'C2_24' not in already_processed:
            already_processed.append('C2_24')
            showIndent(outfile, level)
            outfile.write('C2_24 = %s,\n' % (self.C2_24,))
        if self.C2_26 is not None and 'C2_26' not in already_processed:
            already_processed.append('C2_26')
            showIndent(outfile, level)
            outfile.write('C2_26 = %s,\n' % (self.C2_26,))
        if self.C2_21 is not None and 'C2_21' not in already_processed:
            already_processed.append('C2_21')
            showIndent(outfile, level)
            outfile.write('C2_21 = %s,\n' % (self.C2_21,))
        if self.C2_22 is not None and 'C2_22' not in already_processed:
            already_processed.append('C2_22')
            showIndent(outfile, level)
            outfile.write('C2_22 = %s,\n' % (self.C2_22,))
        if self.C2_T6 is not None and 'C2_T6' not in already_processed:
            already_processed.append('C2_T6')
            showIndent(outfile, level)
            outfile.write('C2_T6 = %s,\n' % (self.C2_T6,))
        if self.C2_8 is not None and 'C2_8' not in already_processed:
            already_processed.append('C2_8')
            showIndent(outfile, level)
            outfile.write('C2_8 = %s,\n' % (self.C2_8,))
        if self.C2_9 is not None and 'C2_9' not in already_processed:
            already_processed.append('C2_9')
            showIndent(outfile, level)
            outfile.write('C2_9 = %s,\n' % (self.C2_9,))
        if self.C2_7 is not None and 'C2_7' not in already_processed:
            already_processed.append('C2_7')
            showIndent(outfile, level)
            outfile.write('C2_7 = %s,\n' % (self.C2_7,))
        if self.C2_120 is not None and 'C2_120' not in already_processed:
            already_processed.append('C2_120')
            showIndent(outfile, level)
            outfile.write('C2_120 = %s,\n' % (self.C2_120,))
        if self.C2_14 is not None and 'C2_14' not in already_processed:
            already_processed.append('C2_14')
            showIndent(outfile, level)
            outfile.write('C2_14 = %s,\n' % (self.C2_14,))
        if self.C2_15 is not None and 'C2_15' not in already_processed:
            already_processed.append('C2_15')
            showIndent(outfile, level)
            outfile.write('C2_15 = %s,\n' % (self.C2_15,))
        if self.C2_16 is not None and 'C2_16' not in already_processed:
            already_processed.append('C2_16')
            showIndent(outfile, level)
            outfile.write('C2_16 = %s,\n' % (self.C2_16,))
        if self.C2_10 is not None and 'C2_10' not in already_processed:
            already_processed.append('C2_10')
            showIndent(outfile, level)
            outfile.write('C2_10 = %s,\n' % (self.C2_10,))
        if self.C2_11 is not None and 'C2_11' not in already_processed:
            already_processed.append('C2_11')
            showIndent(outfile, level)
            outfile.write('C2_11 = %s,\n' % (self.C2_11,))
        if self.C2_12 is not None and 'C2_12' not in already_processed:
            already_processed.append('C2_12')
            showIndent(outfile, level)
            outfile.write('C2_12 = %s,\n' % (self.C2_12,))
        if self.C2_13 is not None and 'C2_13' not in already_processed:
            already_processed.append('C2_13')
            showIndent(outfile, level)
            outfile.write('C2_13 = %s,\n' % (self.C2_13,))
        if self.C2_51 is not None and 'C2_51' not in already_processed:
            already_processed.append('C2_51')
            showIndent(outfile, level)
            outfile.write('C2_51 = %s,\n' % (self.C2_51,))
        if self.C2_52 is not None and 'C2_52' not in already_processed:
            already_processed.append('C2_52')
            showIndent(outfile, level)
            outfile.write('C2_52 = %s,\n' % (self.C2_52,))
        if self.C2_54 is not None and 'C2_54' not in already_processed:
            already_processed.append('C2_54')
            showIndent(outfile, level)
            outfile.write('C2_54 = %s,\n' % (self.C2_54,))
        if self.C2_56 is not None and 'C2_56' not in already_processed:
            already_processed.append('C2_56')
            showIndent(outfile, level)
            outfile.write('C2_56 = %s,\n' % (self.C2_56,))
        if self.C2_36 is not None and 'C2_36' not in already_processed:
            already_processed.append('C2_36')
            showIndent(outfile, level)
            outfile.write('C2_36 = %s,\n' % (self.C2_36,))
        if self.C2_34 is not None and 'C2_34' not in already_processed:
            already_processed.append('C2_34')
            showIndent(outfile, level)
            outfile.write('C2_34 = %s,\n' % (self.C2_34,))
        if self.C2_32 is not None and 'C2_32' not in already_processed:
            already_processed.append('C2_32')
            showIndent(outfile, level)
            outfile.write('C2_32 = %s,\n' % (self.C2_32,))
        if self.C2_31 is not None and 'C2_31' not in already_processed:
            already_processed.append('C2_31')
            showIndent(outfile, level)
            outfile.write('C2_31 = %s,\n' % (self.C2_31,))
        if self.C2_130 is not None and 'C2_130' not in already_processed:
            already_processed.append('C2_130')
            showIndent(outfile, level)
            outfile.write('C2_130 = %s,\n' % (self.C2_130,))
        if self.C2_110 is not None and 'C2_110' not in already_processed:
            already_processed.append('C2_110')
            showIndent(outfile, level)
            outfile.write('C2_110 = %s,\n' % (self.C2_110,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C2_46')
        if value is not None and 'C2_46' not in already_processed:
            already_processed.append('C2_46')
            self.C2_46 = value
        value = attrs.get('C2_44')
        if value is not None and 'C2_44' not in already_processed:
            already_processed.append('C2_44')
            self.C2_44 = value
        value = attrs.get('C2_42')
        if value is not None and 'C2_42' not in already_processed:
            already_processed.append('C2_42')
            self.C2_42 = value
        value = attrs.get('C2_41')
        if value is not None and 'C2_41' not in already_processed:
            already_processed.append('C2_41')
            self.C2_41 = value
        value = attrs.get('C2_24')
        if value is not None and 'C2_24' not in already_processed:
            already_processed.append('C2_24')
            self.C2_24 = value
        value = attrs.get('C2_26')
        if value is not None and 'C2_26' not in already_processed:
            already_processed.append('C2_26')
            self.C2_26 = value
        value = attrs.get('C2_21')
        if value is not None and 'C2_21' not in already_processed:
            already_processed.append('C2_21')
            self.C2_21 = value
        value = attrs.get('C2_22')
        if value is not None and 'C2_22' not in already_processed:
            already_processed.append('C2_22')
            self.C2_22 = value
        value = attrs.get('C2_T6')
        if value is not None and 'C2_T6' not in already_processed:
            already_processed.append('C2_T6')
            self.C2_T6 = value
        value = attrs.get('C2_8')
        if value is not None and 'C2_8' not in already_processed:
            already_processed.append('C2_8')
            self.C2_8 = value
        value = attrs.get('C2_9')
        if value is not None and 'C2_9' not in already_processed:
            already_processed.append('C2_9')
            self.C2_9 = value
        value = attrs.get('C2_7')
        if value is not None and 'C2_7' not in already_processed:
            already_processed.append('C2_7')
            self.C2_7 = value
        value = attrs.get('C2_120')
        if value is not None and 'C2_120' not in already_processed:
            already_processed.append('C2_120')
            self.C2_120 = value
        value = attrs.get('C2_14')
        if value is not None and 'C2_14' not in already_processed:
            already_processed.append('C2_14')
            self.C2_14 = value
        value = attrs.get('C2_15')
        if value is not None and 'C2_15' not in already_processed:
            already_processed.append('C2_15')
            self.C2_15 = value
        value = attrs.get('C2_16')
        if value is not None and 'C2_16' not in already_processed:
            already_processed.append('C2_16')
            self.C2_16 = value
        value = attrs.get('C2_10')
        if value is not None and 'C2_10' not in already_processed:
            already_processed.append('C2_10')
            self.C2_10 = value
        value = attrs.get('C2_11')
        if value is not None and 'C2_11' not in already_processed:
            already_processed.append('C2_11')
            self.C2_11 = value
        value = attrs.get('C2_12')
        if value is not None and 'C2_12' not in already_processed:
            already_processed.append('C2_12')
            self.C2_12 = value
        value = attrs.get('C2_13')
        if value is not None and 'C2_13' not in already_processed:
            already_processed.append('C2_13')
            self.C2_13 = value
        value = attrs.get('C2_51')
        if value is not None and 'C2_51' not in already_processed:
            already_processed.append('C2_51')
            self.C2_51 = value
        value = attrs.get('C2_52')
        if value is not None and 'C2_52' not in already_processed:
            already_processed.append('C2_52')
            self.C2_52 = value
        value = attrs.get('C2_54')
        if value is not None and 'C2_54' not in already_processed:
            already_processed.append('C2_54')
            self.C2_54 = value
        value = attrs.get('C2_56')
        if value is not None and 'C2_56' not in already_processed:
            already_processed.append('C2_56')
            self.C2_56 = value
        value = attrs.get('C2_36')
        if value is not None and 'C2_36' not in already_processed:
            already_processed.append('C2_36')
            self.C2_36 = value
        value = attrs.get('C2_34')
        if value is not None and 'C2_34' not in already_processed:
            already_processed.append('C2_34')
            self.C2_34 = value
        value = attrs.get('C2_32')
        if value is not None and 'C2_32' not in already_processed:
            already_processed.append('C2_32')
            self.C2_32 = value
        value = attrs.get('C2_31')
        if value is not None and 'C2_31' not in already_processed:
            already_processed.append('C2_31')
            self.C2_31 = value
        value = attrs.get('C2_130')
        if value is not None and 'C2_130' not in already_processed:
            already_processed.append('C2_130')
            self.C2_130 = value
        value = attrs.get('C2_110')
        if value is not None and 'C2_110' not in already_processed:
            already_processed.append('C2_110')
            self.C2_110 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC2Type


class AngajatorC3Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C3_aj_suma=None, C3_41=None, C3_42=None, C3_43=None, C3_44=None, C3_34=None, C3_total=None, C3_14=None, C3_24=None, C3_aj_nr=None, C3_13=None, C3_12=None, C3_11=None, C3_22=None, C3_23=None, C3_33=None, C3_21=None, C3_31=None, C3_suma=None, C3_32=None, valueOf_=None):
        self.C3_aj_suma = _cast(None, C3_aj_suma)
        self.C3_41 = _cast(None, C3_41)
        self.C3_42 = _cast(None, C3_42)
        self.C3_43 = _cast(None, C3_43)
        self.C3_44 = _cast(None, C3_44)
        self.C3_34 = _cast(None, C3_34)
        self.C3_total = _cast(None, C3_total)
        self.C3_14 = _cast(None, C3_14)
        self.C3_24 = _cast(None, C3_24)
        self.C3_aj_nr = _cast(None, C3_aj_nr)
        self.C3_13 = _cast(None, C3_13)
        self.C3_12 = _cast(None, C3_12)
        self.C3_11 = _cast(None, C3_11)
        self.C3_22 = _cast(None, C3_22)
        self.C3_23 = _cast(None, C3_23)
        self.C3_33 = _cast(None, C3_33)
        self.C3_21 = _cast(None, C3_21)
        self.C3_31 = _cast(None, C3_31)
        self.C3_suma = _cast(None, C3_suma)
        self.C3_32 = _cast(None, C3_32)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC3Type.subclass:
            return AngajatorC3Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC3Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C3_aj_suma(self): return self.C3_aj_suma
    def set_C3_aj_suma(self, C3_aj_suma): self.C3_aj_suma = C3_aj_suma
    def get_C3_41(self): return self.C3_41
    def set_C3_41(self, C3_41): self.C3_41 = C3_41
    def get_C3_42(self): return self.C3_42
    def set_C3_42(self, C3_42): self.C3_42 = C3_42
    def get_C3_43(self): return self.C3_43
    def set_C3_43(self, C3_43): self.C3_43 = C3_43
    def get_C3_44(self): return self.C3_44
    def set_C3_44(self, C3_44): self.C3_44 = C3_44
    def get_C3_34(self): return self.C3_34
    def set_C3_34(self, C3_34): self.C3_34 = C3_34
    def get_C3_total(self): return self.C3_total
    def set_C3_total(self, C3_total): self.C3_total = C3_total
    def get_C3_14(self): return self.C3_14
    def set_C3_14(self, C3_14): self.C3_14 = C3_14
    def get_C3_24(self): return self.C3_24
    def set_C3_24(self, C3_24): self.C3_24 = C3_24
    def get_C3_aj_nr(self): return self.C3_aj_nr
    def set_C3_aj_nr(self, C3_aj_nr): self.C3_aj_nr = C3_aj_nr
    def get_C3_13(self): return self.C3_13
    def set_C3_13(self, C3_13): self.C3_13 = C3_13
    def get_C3_12(self): return self.C3_12
    def set_C3_12(self, C3_12): self.C3_12 = C3_12
    def get_C3_11(self): return self.C3_11
    def set_C3_11(self, C3_11): self.C3_11 = C3_11
    def get_C3_22(self): return self.C3_22
    def set_C3_22(self, C3_22): self.C3_22 = C3_22
    def get_C3_23(self): return self.C3_23
    def set_C3_23(self, C3_23): self.C3_23 = C3_23
    def get_C3_33(self): return self.C3_33
    def set_C3_33(self, C3_33): self.C3_33 = C3_33
    def get_C3_21(self): return self.C3_21
    def set_C3_21(self, C3_21): self.C3_21 = C3_21
    def get_C3_31(self): return self.C3_31
    def set_C3_31(self, C3_31): self.C3_31 = C3_31
    def get_C3_suma(self): return self.C3_suma
    def set_C3_suma(self, C3_suma): self.C3_suma = C3_suma
    def get_C3_32(self): return self.C3_32
    def set_C3_32(self, C3_32): self.C3_32 = C3_32
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC3Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC3Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC3Type'):
        if self.C3_aj_suma is not None and 'C3_aj_suma' not in already_processed:
            already_processed.append('C3_aj_suma')
            outfile.write(' C3_aj_suma=%s' % (quote_attrib(self.C3_aj_suma), ))
        if self.C3_41 is not None and 'C3_41' not in already_processed:
            already_processed.append('C3_41')
            outfile.write(' C3_41=%s' % (quote_attrib(self.C3_41), ))
        if self.C3_42 is not None and 'C3_42' not in already_processed:
            already_processed.append('C3_42')
            outfile.write(' C3_42=%s' % (quote_attrib(self.C3_42), ))
        if self.C3_43 is not None and 'C3_43' not in already_processed:
            already_processed.append('C3_43')
            outfile.write(' C3_43=%s' % (quote_attrib(self.C3_43), ))
        if self.C3_44 is not None and 'C3_44' not in already_processed:
            already_processed.append('C3_44')
            outfile.write(' C3_44=%s' % (quote_attrib(self.C3_44), ))
        if self.C3_34 is not None and 'C3_34' not in already_processed:
            already_processed.append('C3_34')
            outfile.write(' C3_34=%s' % (quote_attrib(self.C3_34), ))
        if self.C3_total is not None and 'C3_total' not in already_processed:
            already_processed.append('C3_total')
            outfile.write(' C3_total=%s' % (quote_attrib(self.C3_total), ))
        if self.C3_14 is not None and 'C3_14' not in already_processed:
            already_processed.append('C3_14')
            outfile.write(' C3_14=%s' % (quote_attrib(self.C3_14), ))
        if self.C3_24 is not None and 'C3_24' not in already_processed:
            already_processed.append('C3_24')
            outfile.write(' C3_24=%s' % (quote_attrib(self.C3_24), ))
        if self.C3_aj_nr is not None and 'C3_aj_nr' not in already_processed:
            already_processed.append('C3_aj_nr')
            outfile.write(' C3_aj_nr=%s' % (quote_attrib(self.C3_aj_nr), ))
        if self.C3_13 is not None and 'C3_13' not in already_processed:
            already_processed.append('C3_13')
            outfile.write(' C3_13=%s' % (quote_attrib(self.C3_13), ))
        if self.C3_12 is not None and 'C3_12' not in already_processed:
            already_processed.append('C3_12')
            outfile.write(' C3_12=%s' % (quote_attrib(self.C3_12), ))
        if self.C3_11 is not None and 'C3_11' not in already_processed:
            already_processed.append('C3_11')
            outfile.write(' C3_11=%s' % (quote_attrib(self.C3_11), ))
        if self.C3_22 is not None and 'C3_22' not in already_processed:
            already_processed.append('C3_22')
            outfile.write(' C3_22=%s' % (quote_attrib(self.C3_22), ))
        if self.C3_23 is not None and 'C3_23' not in already_processed:
            already_processed.append('C3_23')
            outfile.write(' C3_23=%s' % (quote_attrib(self.C3_23), ))
        if self.C3_33 is not None and 'C3_33' not in already_processed:
            already_processed.append('C3_33')
            outfile.write(' C3_33=%s' % (quote_attrib(self.C3_33), ))
        if self.C3_21 is not None and 'C3_21' not in already_processed:
            already_processed.append('C3_21')
            outfile.write(' C3_21=%s' % (quote_attrib(self.C3_21), ))
        if self.C3_31 is not None and 'C3_31' not in already_processed:
            already_processed.append('C3_31')
            outfile.write(' C3_31=%s' % (quote_attrib(self.C3_31), ))
        if self.C3_suma is not None and 'C3_suma' not in already_processed:
            already_processed.append('C3_suma')
            outfile.write(' C3_suma=%s' % (quote_attrib(self.C3_suma), ))
        if self.C3_32 is not None and 'C3_32' not in already_processed:
            already_processed.append('C3_32')
            outfile.write(' C3_32=%s' % (quote_attrib(self.C3_32), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC3Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC3Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C3_aj_suma is not None and 'C3_aj_suma' not in already_processed:
            already_processed.append('C3_aj_suma')
            showIndent(outfile, level)
            outfile.write('C3_aj_suma = %s,\n' % (self.C3_aj_suma,))
        if self.C3_41 is not None and 'C3_41' not in already_processed:
            already_processed.append('C3_41')
            showIndent(outfile, level)
            outfile.write('C3_41 = %s,\n' % (self.C3_41,))
        if self.C3_42 is not None and 'C3_42' not in already_processed:
            already_processed.append('C3_42')
            showIndent(outfile, level)
            outfile.write('C3_42 = %s,\n' % (self.C3_42,))
        if self.C3_43 is not None and 'C3_43' not in already_processed:
            already_processed.append('C3_43')
            showIndent(outfile, level)
            outfile.write('C3_43 = %s,\n' % (self.C3_43,))
        if self.C3_44 is not None and 'C3_44' not in already_processed:
            already_processed.append('C3_44')
            showIndent(outfile, level)
            outfile.write('C3_44 = %s,\n' % (self.C3_44,))
        if self.C3_34 is not None and 'C3_34' not in already_processed:
            already_processed.append('C3_34')
            showIndent(outfile, level)
            outfile.write('C3_34 = %s,\n' % (self.C3_34,))
        if self.C3_total is not None and 'C3_total' not in already_processed:
            already_processed.append('C3_total')
            showIndent(outfile, level)
            outfile.write('C3_total = %s,\n' % (self.C3_total,))
        if self.C3_14 is not None and 'C3_14' not in already_processed:
            already_processed.append('C3_14')
            showIndent(outfile, level)
            outfile.write('C3_14 = %s,\n' % (self.C3_14,))
        if self.C3_24 is not None and 'C3_24' not in already_processed:
            already_processed.append('C3_24')
            showIndent(outfile, level)
            outfile.write('C3_24 = %s,\n' % (self.C3_24,))
        if self.C3_aj_nr is not None and 'C3_aj_nr' not in already_processed:
            already_processed.append('C3_aj_nr')
            showIndent(outfile, level)
            outfile.write('C3_aj_nr = %s,\n' % (self.C3_aj_nr,))
        if self.C3_13 is not None and 'C3_13' not in already_processed:
            already_processed.append('C3_13')
            showIndent(outfile, level)
            outfile.write('C3_13 = %s,\n' % (self.C3_13,))
        if self.C3_12 is not None and 'C3_12' not in already_processed:
            already_processed.append('C3_12')
            showIndent(outfile, level)
            outfile.write('C3_12 = %s,\n' % (self.C3_12,))
        if self.C3_11 is not None and 'C3_11' not in already_processed:
            already_processed.append('C3_11')
            showIndent(outfile, level)
            outfile.write('C3_11 = %s,\n' % (self.C3_11,))
        if self.C3_22 is not None and 'C3_22' not in already_processed:
            already_processed.append('C3_22')
            showIndent(outfile, level)
            outfile.write('C3_22 = %s,\n' % (self.C3_22,))
        if self.C3_23 is not None and 'C3_23' not in already_processed:
            already_processed.append('C3_23')
            showIndent(outfile, level)
            outfile.write('C3_23 = %s,\n' % (self.C3_23,))
        if self.C3_33 is not None and 'C3_33' not in already_processed:
            already_processed.append('C3_33')
            showIndent(outfile, level)
            outfile.write('C3_33 = %s,\n' % (self.C3_33,))
        if self.C3_21 is not None and 'C3_21' not in already_processed:
            already_processed.append('C3_21')
            showIndent(outfile, level)
            outfile.write('C3_21 = %s,\n' % (self.C3_21,))
        if self.C3_31 is not None and 'C3_31' not in already_processed:
            already_processed.append('C3_31')
            showIndent(outfile, level)
            outfile.write('C3_31 = %s,\n' % (self.C3_31,))
        if self.C3_suma is not None and 'C3_suma' not in already_processed:
            already_processed.append('C3_suma')
            showIndent(outfile, level)
            outfile.write('C3_suma = %s,\n' % (self.C3_suma,))
        if self.C3_32 is not None and 'C3_32' not in already_processed:
            already_processed.append('C3_32')
            showIndent(outfile, level)
            outfile.write('C3_32 = %s,\n' % (self.C3_32,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C3_aj_suma')
        if value is not None and 'C3_aj_suma' not in already_processed:
            already_processed.append('C3_aj_suma')
            self.C3_aj_suma = value
        value = attrs.get('C3_41')
        if value is not None and 'C3_41' not in already_processed:
            already_processed.append('C3_41')
            self.C3_41 = value
        value = attrs.get('C3_42')
        if value is not None and 'C3_42' not in already_processed:
            already_processed.append('C3_42')
            self.C3_42 = value
        value = attrs.get('C3_43')
        if value is not None and 'C3_43' not in already_processed:
            already_processed.append('C3_43')
            self.C3_43 = value
        value = attrs.get('C3_44')
        if value is not None and 'C3_44' not in already_processed:
            already_processed.append('C3_44')
            self.C3_44 = value
        value = attrs.get('C3_34')
        if value is not None and 'C3_34' not in already_processed:
            already_processed.append('C3_34')
            self.C3_34 = value
        value = attrs.get('C3_total')
        if value is not None and 'C3_total' not in already_processed:
            already_processed.append('C3_total')
            self.C3_total = value
        value = attrs.get('C3_14')
        if value is not None and 'C3_14' not in already_processed:
            already_processed.append('C3_14')
            self.C3_14 = value
        value = attrs.get('C3_24')
        if value is not None and 'C3_24' not in already_processed:
            already_processed.append('C3_24')
            self.C3_24 = value
        value = attrs.get('C3_aj_nr')
        if value is not None and 'C3_aj_nr' not in already_processed:
            already_processed.append('C3_aj_nr')
            self.C3_aj_nr = value
        value = attrs.get('C3_13')
        if value is not None and 'C3_13' not in already_processed:
            already_processed.append('C3_13')
            self.C3_13 = value
        value = attrs.get('C3_12')
        if value is not None and 'C3_12' not in already_processed:
            already_processed.append('C3_12')
            self.C3_12 = value
        value = attrs.get('C3_11')
        if value is not None and 'C3_11' not in already_processed:
            already_processed.append('C3_11')
            self.C3_11 = value
        value = attrs.get('C3_22')
        if value is not None and 'C3_22' not in already_processed:
            already_processed.append('C3_22')
            self.C3_22 = value
        value = attrs.get('C3_23')
        if value is not None and 'C3_23' not in already_processed:
            already_processed.append('C3_23')
            self.C3_23 = value
        value = attrs.get('C3_33')
        if value is not None and 'C3_33' not in already_processed:
            already_processed.append('C3_33')
            self.C3_33 = value
        value = attrs.get('C3_21')
        if value is not None and 'C3_21' not in already_processed:
            already_processed.append('C3_21')
            self.C3_21 = value
        value = attrs.get('C3_31')
        if value is not None and 'C3_31' not in already_processed:
            already_processed.append('C3_31')
            self.C3_31 = value
        value = attrs.get('C3_suma')
        if value is not None and 'C3_suma' not in already_processed:
            already_processed.append('C3_suma')
            self.C3_suma = value
        value = attrs.get('C3_32')
        if value is not None and 'C3_32' not in already_processed:
            already_processed.append('C3_32')
            self.C3_32 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC3Type


class AngajatorC4Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C4_scutitaSo=None, valueOf_=None):
        self.C4_scutitaSo = _cast(None, C4_scutitaSo)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC4Type.subclass:
            return AngajatorC4Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC4Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C4_scutitaSo(self): return self.C4_scutitaSo
    def set_C4_scutitaSo(self, C4_scutitaSo): self.C4_scutitaSo = C4_scutitaSo
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC4Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC4Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC4Type'):
        if self.C4_scutitaSo is not None and 'C4_scutitaSo' not in already_processed:
            already_processed.append('C4_scutitaSo')
            outfile.write(' C4_scutitaSo=%s' % (quote_attrib(self.C4_scutitaSo), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC4Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC4Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C4_scutitaSo is not None and 'C4_scutitaSo' not in already_processed:
            already_processed.append('C4_scutitaSo')
            showIndent(outfile, level)
            outfile.write('C4_scutitaSo = %s,\n' % (self.C4_scutitaSo,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C4_scutitaSo')
        if value is not None and 'C4_scutitaSo' not in already_processed:
            already_processed.append('C4_scutitaSo')
            self.C4_scutitaSo = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC4Type


class AngajatorC5Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C5_subv=None, C5_restituit=None, C5_recuperat=None, valueOf_=None):
        self.C5_subv = _cast(None, C5_subv)
        self.C5_restituit = _cast(None, C5_restituit)
        self.C5_recuperat = _cast(None, C5_recuperat)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC5Type.subclass:
            return AngajatorC5Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC5Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C5_subv(self): return self.C5_subv
    def set_C5_subv(self, C5_subv): self.C5_subv = C5_subv
    def get_C5_restituit(self): return self.C5_restituit
    def set_C5_restituit(self, C5_restituit): self.C5_restituit = C5_restituit
    def get_C5_recuperat(self): return self.C5_recuperat
    def set_C5_recuperat(self, C5_recuperat): self.C5_recuperat = C5_recuperat
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC5Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC5Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC5Type'):
        if self.C5_subv is not None and 'C5_subv' not in already_processed:
            already_processed.append('C5_subv')
            outfile.write(' C5_subv=%s' % (quote_attrib(self.C5_subv), ))
        if self.C5_restituit is not None and 'C5_restituit' not in already_processed:
            already_processed.append('C5_restituit')
            outfile.write(' C5_restituit=%s' % (quote_attrib(self.C5_restituit), ))
        if self.C5_recuperat is not None and 'C5_recuperat' not in already_processed:
            already_processed.append('C5_recuperat')
            outfile.write(' C5_recuperat=%s' % (quote_attrib(self.C5_recuperat), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC5Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC5Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C5_subv is not None and 'C5_subv' not in already_processed:
            already_processed.append('C5_subv')
            showIndent(outfile, level)
            outfile.write('C5_subv = %s,\n' % (self.C5_subv,))
        if self.C5_restituit is not None and 'C5_restituit' not in already_processed:
            already_processed.append('C5_restituit')
            showIndent(outfile, level)
            outfile.write('C5_restituit = %s,\n' % (self.C5_restituit,))
        if self.C5_recuperat is not None and 'C5_recuperat' not in already_processed:
            already_processed.append('C5_recuperat')
            showIndent(outfile, level)
            outfile.write('C5_recuperat = %s,\n' % (self.C5_recuperat,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C5_subv')
        if value is not None and 'C5_subv' not in already_processed:
            already_processed.append('C5_subv')
            self.C5_subv = value
        value = attrs.get('C5_restituit')
        if value is not None and 'C5_restituit' not in already_processed:
            already_processed.append('C5_restituit')
            self.C5_restituit = value
        value = attrs.get('C5_recuperat')
        if value is not None and 'C5_recuperat' not in already_processed:
            already_processed.append('C5_recuperat')
            self.C5_recuperat = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC5Type


class AngajatorC6Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C6_baza=None, C6_ct=None, valueOf_=None):
        self.C6_baza = _cast(None, C6_baza)
        self.C6_ct = _cast(None, C6_ct)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC6Type.subclass:
            return AngajatorC6Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC6Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C6_baza(self): return self.C6_baza
    def set_C6_baza(self, C6_baza): self.C6_baza = C6_baza
    def get_C6_ct(self): return self.C6_ct
    def set_C6_ct(self, C6_ct): self.C6_ct = C6_ct
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC6Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC6Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC6Type'):
        outfile.write(' C6_baza=%s' % (quote_attrib(self.C6_baza), ))
        outfile.write(' C6_ct=%s' % (quote_attrib(self.C6_ct), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC6Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC6Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C6_baza is not None and 'C6_baza' not in already_processed:
            already_processed.append('C6_baza')
            showIndent(outfile, level)
            outfile.write('C6_baza = %s,\n' % (self.C6_baza,))
        if self.C6_ct is not None and 'C6_ct' not in already_processed:
            already_processed.append('C6_ct')
            showIndent(outfile, level)
            outfile.write('C6_ct = %s,\n' % (self.C6_ct,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C6_baza')
        if value is not None and 'C6_baza' not in already_processed:
            already_processed.append('C6_baza')
            self.C6_baza = value
        value = attrs.get('C6_ct')
        if value is not None and 'C6_ct' not in already_processed:
            already_processed.append('C6_ct')
            self.C6_ct = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC6Type


class AngajatorC7Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C7_ct=None, C7_baza=None, valueOf_=None):
        self.C7_ct = _cast(None, C7_ct)
        self.C7_baza = _cast(None, C7_baza)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorC7Type.subclass:
            return AngajatorC7Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorC7Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C7_ct(self): return self.C7_ct
    def set_C7_ct(self, C7_ct): self.C7_ct = C7_ct
    def get_C7_baza(self): return self.C7_baza
    def set_C7_baza(self, C7_baza): self.C7_baza = C7_baza
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorC7Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorC7Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorC7Type'):
        if self.C7_ct is not None and 'C7_ct' not in already_processed:
            already_processed.append('C7_ct')
            outfile.write(' C7_ct=%s' % (quote_attrib(self.C7_ct), ))
        if self.C7_baza is not None and 'C7_baza' not in already_processed:
            already_processed.append('C7_baza')
            outfile.write(' C7_baza=%s' % (quote_attrib(self.C7_baza), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorC7Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorC7Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C7_ct is not None and 'C7_ct' not in already_processed:
            already_processed.append('C7_ct')
            showIndent(outfile, level)
            outfile.write('C7_ct = %s,\n' % (self.C7_ct,))
        if self.C7_baza is not None and 'C7_baza' not in already_processed:
            already_processed.append('C7_baza')
            showIndent(outfile, level)
            outfile.write('C7_baza = %s,\n' % (self.C7_baza,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C7_ct')
        if value is not None and 'C7_ct' not in already_processed:
            already_processed.append('C7_ct')
            self.C7_ct = value
        value = attrs.get('C7_baza')
        if value is not None and 'C7_baza' not in already_processed:
            already_processed.append('C7_baza')
            self.C7_baza = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorC7Type


class AngajatorDType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, D4=None, D2=None, D3=None, D1=None, valueOf_=None):
        self.D4 = _cast(None, D4)
        self.D2 = _cast(None, D2)
        self.D3 = _cast(None, D3)
        self.D1 = _cast(None, D1)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorDType.subclass:
            return AngajatorDType.subclass(*args_, **kwargs_)
        else:
            return AngajatorDType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_D4(self): return self.D4
    def set_D4(self, D4): self.D4 = D4
    def get_D2(self): return self.D2
    def set_D2(self, D2): self.D2 = D2
    def get_D3(self): return self.D3
    def set_D3(self, D3): self.D3 = D3
    def get_D1(self): return self.D1
    def set_D1(self, D1): self.D1 = D1
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorDType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorDType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorDType'):
        if self.D4 is not None and 'D4' not in already_processed:
            already_processed.append('D4')
            outfile.write(' D4=%s' % (quote_attrib(self.D4), ))
        if self.D2 is not None and 'D2' not in already_processed:
            already_processed.append('D2')
            outfile.write(' D2=%s' % (quote_attrib(self.D2), ))
        if self.D3 is not None and 'D3' not in already_processed:
            already_processed.append('D3')
            outfile.write(' D3=%s' % (quote_attrib(self.D3), ))
        if self.D1 is not None and 'D1' not in already_processed:
            already_processed.append('D1')
            outfile.write(' D1=%s' % (quote_attrib(self.D1), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorDType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorDType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.D4 is not None and 'D4' not in already_processed:
            already_processed.append('D4')
            showIndent(outfile, level)
            outfile.write('D4 = %s,\n' % (self.D4,))
        if self.D2 is not None and 'D2' not in already_processed:
            already_processed.append('D2')
            showIndent(outfile, level)
            outfile.write('D2 = %s,\n' % (self.D2,))
        if self.D3 is not None and 'D3' not in already_processed:
            already_processed.append('D3')
            showIndent(outfile, level)
            outfile.write('D3 = %s,\n' % (self.D3,))
        if self.D1 is not None and 'D1' not in already_processed:
            already_processed.append('D1')
            showIndent(outfile, level)
            outfile.write('D1 = %s,\n' % (self.D1,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('D4')
        if value is not None and 'D4' not in already_processed:
            already_processed.append('D4')
            self.D4 = value
        value = attrs.get('D2')
        if value is not None and 'D2' not in already_processed:
            already_processed.append('D2')
            self.D2 = value
        value = attrs.get('D3')
        if value is not None and 'D3' not in already_processed:
            already_processed.append('D3')
            self.D3 = value
        value = attrs.get('D1')
        if value is not None and 'D1' not in already_processed:
            already_processed.append('D1')
            self.D1 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorDType


class AngajatorE1Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, E1_venit=None, E1_ct=None, E1_baza=None, valueOf_=None):
        self.E1_venit = _cast(None, E1_venit)
        self.E1_ct = _cast(None, E1_ct)
        self.E1_baza = _cast(None, E1_baza)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorE1Type.subclass:
            return AngajatorE1Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorE1Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_E1_venit(self): return self.E1_venit
    def set_E1_venit(self, E1_venit): self.E1_venit = E1_venit
    def get_E1_ct(self): return self.E1_ct
    def set_E1_ct(self, E1_ct): self.E1_ct = E1_ct
    def get_E1_baza(self): return self.E1_baza
    def set_E1_baza(self, E1_baza): self.E1_baza = E1_baza
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorE1Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorE1Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorE1Type'):
        if self.E1_venit is not None and 'E1_venit' not in already_processed:
            already_processed.append('E1_venit')
            outfile.write(' E1_venit=%s' % (quote_attrib(self.E1_venit), ))
        if self.E1_ct is not None and 'E1_ct' not in already_processed:
            already_processed.append('E1_ct')
            outfile.write(' E1_ct=%s' % (quote_attrib(self.E1_ct), ))
        if self.E1_baza is not None and 'E1_baza' not in already_processed:
            already_processed.append('E1_baza')
            outfile.write(' E1_baza=%s' % (quote_attrib(self.E1_baza), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorE1Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorE1Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.E1_venit is not None and 'E1_venit' not in already_processed:
            already_processed.append('E1_venit')
            showIndent(outfile, level)
            outfile.write('E1_venit = %s,\n' % (self.E1_venit,))
        if self.E1_ct is not None and 'E1_ct' not in already_processed:
            already_processed.append('E1_ct')
            showIndent(outfile, level)
            outfile.write('E1_ct = %s,\n' % (self.E1_ct,))
        if self.E1_baza is not None and 'E1_baza' not in already_processed:
            already_processed.append('E1_baza')
            showIndent(outfile, level)
            outfile.write('E1_baza = %s,\n' % (self.E1_baza,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('E1_venit')
        if value is not None and 'E1_venit' not in already_processed:
            already_processed.append('E1_venit')
            self.E1_venit = value
        value = attrs.get('E1_ct')
        if value is not None and 'E1_ct' not in already_processed:
            already_processed.append('E1_ct')
            self.E1_ct = value
        value = attrs.get('E1_baza')
        if value is not None and 'E1_baza' not in already_processed:
            already_processed.append('E1_baza')
            self.E1_baza = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorE1Type


class AngajatorE2Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, E2_32=None, E2_120=None, E2_52=None, E2_36=None, E2_51=None, E2_56=None, E2_31=None, E2_54=None, E2_16=None, E2_14=None, E2_12=None, E2_10=None, E2_11=None, E2_8=None, E2_9=None, E2_110=None, E2_7=None, E2_130=None, E2_41=None, E2_42=None, E2_44=None, E2_46=None, E2_66=None, E2_34=None, E2_22=None, E2_21=None, E2_26=None, E2_24=None, valueOf_=None):
        self.E2_32 = _cast(None, E2_32)
        self.E2_120 = _cast(None, E2_120)
        self.E2_52 = _cast(None, E2_52)
        self.E2_36 = _cast(None, E2_36)
        self.E2_51 = _cast(None, E2_51)
        self.E2_56 = _cast(None, E2_56)
        self.E2_31 = _cast(None, E2_31)
        self.E2_54 = _cast(None, E2_54)
        self.E2_16 = _cast(None, E2_16)
        self.E2_14 = _cast(None, E2_14)
        self.E2_12 = _cast(None, E2_12)
        self.E2_10 = _cast(None, E2_10)
        self.E2_11 = _cast(None, E2_11)
        self.E2_8 = _cast(None, E2_8)
        self.E2_9 = _cast(None, E2_9)
        self.E2_110 = _cast(None, E2_110)
        self.E2_7 = _cast(None, E2_7)
        self.E2_130 = _cast(None, E2_130)
        self.E2_41 = _cast(None, E2_41)
        self.E2_42 = _cast(None, E2_42)
        self.E2_44 = _cast(None, E2_44)
        self.E2_46 = _cast(None, E2_46)
        self.E2_66 = _cast(None, E2_66)
        self.E2_34 = _cast(None, E2_34)
        self.E2_22 = _cast(None, E2_22)
        self.E2_21 = _cast(None, E2_21)
        self.E2_26 = _cast(None, E2_26)
        self.E2_24 = _cast(None, E2_24)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorE2Type.subclass:
            return AngajatorE2Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorE2Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_E2_32(self): return self.E2_32
    def set_E2_32(self, E2_32): self.E2_32 = E2_32
    def get_E2_120(self): return self.E2_120
    def set_E2_120(self, E2_120): self.E2_120 = E2_120
    def get_E2_52(self): return self.E2_52
    def set_E2_52(self, E2_52): self.E2_52 = E2_52
    def get_E2_36(self): return self.E2_36
    def set_E2_36(self, E2_36): self.E2_36 = E2_36
    def get_E2_51(self): return self.E2_51
    def set_E2_51(self, E2_51): self.E2_51 = E2_51
    def get_E2_56(self): return self.E2_56
    def set_E2_56(self, E2_56): self.E2_56 = E2_56
    def get_E2_31(self): return self.E2_31
    def set_E2_31(self, E2_31): self.E2_31 = E2_31
    def get_E2_54(self): return self.E2_54
    def set_E2_54(self, E2_54): self.E2_54 = E2_54
    def get_E2_16(self): return self.E2_16
    def set_E2_16(self, E2_16): self.E2_16 = E2_16
    def get_E2_14(self): return self.E2_14
    def set_E2_14(self, E2_14): self.E2_14 = E2_14
    def get_E2_12(self): return self.E2_12
    def set_E2_12(self, E2_12): self.E2_12 = E2_12
    def get_E2_10(self): return self.E2_10
    def set_E2_10(self, E2_10): self.E2_10 = E2_10
    def get_E2_11(self): return self.E2_11
    def set_E2_11(self, E2_11): self.E2_11 = E2_11
    def get_E2_8(self): return self.E2_8
    def set_E2_8(self, E2_8): self.E2_8 = E2_8
    def get_E2_9(self): return self.E2_9
    def set_E2_9(self, E2_9): self.E2_9 = E2_9
    def get_E2_110(self): return self.E2_110
    def set_E2_110(self, E2_110): self.E2_110 = E2_110
    def get_E2_7(self): return self.E2_7
    def set_E2_7(self, E2_7): self.E2_7 = E2_7
    def get_E2_130(self): return self.E2_130
    def set_E2_130(self, E2_130): self.E2_130 = E2_130
    def get_E2_41(self): return self.E2_41
    def set_E2_41(self, E2_41): self.E2_41 = E2_41
    def get_E2_42(self): return self.E2_42
    def set_E2_42(self, E2_42): self.E2_42 = E2_42
    def get_E2_44(self): return self.E2_44
    def set_E2_44(self, E2_44): self.E2_44 = E2_44
    def get_E2_46(self): return self.E2_46
    def set_E2_46(self, E2_46): self.E2_46 = E2_46
    def get_E2_66(self): return self.E2_66
    def set_E2_66(self, E2_66): self.E2_66 = E2_66
    def get_E2_34(self): return self.E2_34
    def set_E2_34(self, E2_34): self.E2_34 = E2_34
    def get_E2_22(self): return self.E2_22
    def set_E2_22(self, E2_22): self.E2_22 = E2_22
    def get_E2_21(self): return self.E2_21
    def set_E2_21(self, E2_21): self.E2_21 = E2_21
    def get_E2_26(self): return self.E2_26
    def set_E2_26(self, E2_26): self.E2_26 = E2_26
    def get_E2_24(self): return self.E2_24
    def set_E2_24(self, E2_24): self.E2_24 = E2_24
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorE2Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorE2Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorE2Type'):
        if self.E2_32 is not None and 'E2_32' not in already_processed:
            already_processed.append('E2_32')
            outfile.write(' E2_32=%s' % (quote_attrib(self.E2_32), ))
        if self.E2_120 is not None and 'E2_120' not in already_processed:
            already_processed.append('E2_120')
            outfile.write(' E2_120=%s' % (quote_attrib(self.E2_120), ))
        if self.E2_52 is not None and 'E2_52' not in already_processed:
            already_processed.append('E2_52')
            outfile.write(' E2_52=%s' % (quote_attrib(self.E2_52), ))
        if self.E2_36 is not None and 'E2_36' not in already_processed:
            already_processed.append('E2_36')
            outfile.write(' E2_36=%s' % (quote_attrib(self.E2_36), ))
        if self.E2_51 is not None and 'E2_51' not in already_processed:
            already_processed.append('E2_51')
            outfile.write(' E2_51=%s' % (quote_attrib(self.E2_51), ))
        if self.E2_56 is not None and 'E2_56' not in already_processed:
            already_processed.append('E2_56')
            outfile.write(' E2_56=%s' % (quote_attrib(self.E2_56), ))
        if self.E2_31 is not None and 'E2_31' not in already_processed:
            already_processed.append('E2_31')
            outfile.write(' E2_31=%s' % (quote_attrib(self.E2_31), ))
        if self.E2_54 is not None and 'E2_54' not in already_processed:
            already_processed.append('E2_54')
            outfile.write(' E2_54=%s' % (quote_attrib(self.E2_54), ))
        if self.E2_16 is not None and 'E2_16' not in already_processed:
            already_processed.append('E2_16')
            outfile.write(' E2_16=%s' % (quote_attrib(self.E2_16), ))
        if self.E2_14 is not None and 'E2_14' not in already_processed:
            already_processed.append('E2_14')
            outfile.write(' E2_14=%s' % (quote_attrib(self.E2_14), ))
        if self.E2_12 is not None and 'E2_12' not in already_processed:
            already_processed.append('E2_12')
            outfile.write(' E2_12=%s' % (quote_attrib(self.E2_12), ))
        if self.E2_10 is not None and 'E2_10' not in already_processed:
            already_processed.append('E2_10')
            outfile.write(' E2_10=%s' % (quote_attrib(self.E2_10), ))
        if self.E2_11 is not None and 'E2_11' not in already_processed:
            already_processed.append('E2_11')
            outfile.write(' E2_11=%s' % (quote_attrib(self.E2_11), ))
        if self.E2_8 is not None and 'E2_8' not in already_processed:
            already_processed.append('E2_8')
            outfile.write(' E2_8=%s' % (quote_attrib(self.E2_8), ))
        if self.E2_9 is not None and 'E2_9' not in already_processed:
            already_processed.append('E2_9')
            outfile.write(' E2_9=%s' % (quote_attrib(self.E2_9), ))
        if self.E2_110 is not None and 'E2_110' not in already_processed:
            already_processed.append('E2_110')
            outfile.write(' E2_110=%s' % (quote_attrib(self.E2_110), ))
        if self.E2_7 is not None and 'E2_7' not in already_processed:
            already_processed.append('E2_7')
            outfile.write(' E2_7=%s' % (quote_attrib(self.E2_7), ))
        if self.E2_130 is not None and 'E2_130' not in already_processed:
            already_processed.append('E2_130')
            outfile.write(' E2_130=%s' % (quote_attrib(self.E2_130), ))
        if self.E2_41 is not None and 'E2_41' not in already_processed:
            already_processed.append('E2_41')
            outfile.write(' E2_41=%s' % (quote_attrib(self.E2_41), ))
        if self.E2_42 is not None and 'E2_42' not in already_processed:
            already_processed.append('E2_42')
            outfile.write(' E2_42=%s' % (quote_attrib(self.E2_42), ))
        if self.E2_44 is not None and 'E2_44' not in already_processed:
            already_processed.append('E2_44')
            outfile.write(' E2_44=%s' % (quote_attrib(self.E2_44), ))
        if self.E2_46 is not None and 'E2_46' not in already_processed:
            already_processed.append('E2_46')
            outfile.write(' E2_46=%s' % (quote_attrib(self.E2_46), ))
        if self.E2_66 is not None and 'E2_66' not in already_processed:
            already_processed.append('E2_66')
            outfile.write(' E2_66=%s' % (quote_attrib(self.E2_66), ))
        if self.E2_34 is not None and 'E2_34' not in already_processed:
            already_processed.append('E2_34')
            outfile.write(' E2_34=%s' % (quote_attrib(self.E2_34), ))
        if self.E2_22 is not None and 'E2_22' not in already_processed:
            already_processed.append('E2_22')
            outfile.write(' E2_22=%s' % (quote_attrib(self.E2_22), ))
        if self.E2_21 is not None and 'E2_21' not in already_processed:
            already_processed.append('E2_21')
            outfile.write(' E2_21=%s' % (quote_attrib(self.E2_21), ))
        if self.E2_26 is not None and 'E2_26' not in already_processed:
            already_processed.append('E2_26')
            outfile.write(' E2_26=%s' % (quote_attrib(self.E2_26), ))
        if self.E2_24 is not None and 'E2_24' not in already_processed:
            already_processed.append('E2_24')
            outfile.write(' E2_24=%s' % (quote_attrib(self.E2_24), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorE2Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorE2Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.E2_32 is not None and 'E2_32' not in already_processed:
            already_processed.append('E2_32')
            showIndent(outfile, level)
            outfile.write('E2_32 = %s,\n' % (self.E2_32,))
        if self.E2_120 is not None and 'E2_120' not in already_processed:
            already_processed.append('E2_120')
            showIndent(outfile, level)
            outfile.write('E2_120 = %s,\n' % (self.E2_120,))
        if self.E2_52 is not None and 'E2_52' not in already_processed:
            already_processed.append('E2_52')
            showIndent(outfile, level)
            outfile.write('E2_52 = %s,\n' % (self.E2_52,))
        if self.E2_36 is not None and 'E2_36' not in already_processed:
            already_processed.append('E2_36')
            showIndent(outfile, level)
            outfile.write('E2_36 = %s,\n' % (self.E2_36,))
        if self.E2_51 is not None and 'E2_51' not in already_processed:
            already_processed.append('E2_51')
            showIndent(outfile, level)
            outfile.write('E2_51 = %s,\n' % (self.E2_51,))
        if self.E2_56 is not None and 'E2_56' not in already_processed:
            already_processed.append('E2_56')
            showIndent(outfile, level)
            outfile.write('E2_56 = %s,\n' % (self.E2_56,))
        if self.E2_31 is not None and 'E2_31' not in already_processed:
            already_processed.append('E2_31')
            showIndent(outfile, level)
            outfile.write('E2_31 = %s,\n' % (self.E2_31,))
        if self.E2_54 is not None and 'E2_54' not in already_processed:
            already_processed.append('E2_54')
            showIndent(outfile, level)
            outfile.write('E2_54 = %s,\n' % (self.E2_54,))
        if self.E2_16 is not None and 'E2_16' not in already_processed:
            already_processed.append('E2_16')
            showIndent(outfile, level)
            outfile.write('E2_16 = %s,\n' % (self.E2_16,))
        if self.E2_14 is not None and 'E2_14' not in already_processed:
            already_processed.append('E2_14')
            showIndent(outfile, level)
            outfile.write('E2_14 = %s,\n' % (self.E2_14,))
        if self.E2_12 is not None and 'E2_12' not in already_processed:
            already_processed.append('E2_12')
            showIndent(outfile, level)
            outfile.write('E2_12 = %s,\n' % (self.E2_12,))
        if self.E2_10 is not None and 'E2_10' not in already_processed:
            already_processed.append('E2_10')
            showIndent(outfile, level)
            outfile.write('E2_10 = %s,\n' % (self.E2_10,))
        if self.E2_11 is not None and 'E2_11' not in already_processed:
            already_processed.append('E2_11')
            showIndent(outfile, level)
            outfile.write('E2_11 = %s,\n' % (self.E2_11,))
        if self.E2_8 is not None and 'E2_8' not in already_processed:
            already_processed.append('E2_8')
            showIndent(outfile, level)
            outfile.write('E2_8 = %s,\n' % (self.E2_8,))
        if self.E2_9 is not None and 'E2_9' not in already_processed:
            already_processed.append('E2_9')
            showIndent(outfile, level)
            outfile.write('E2_9 = %s,\n' % (self.E2_9,))
        if self.E2_110 is not None and 'E2_110' not in already_processed:
            already_processed.append('E2_110')
            showIndent(outfile, level)
            outfile.write('E2_110 = %s,\n' % (self.E2_110,))
        if self.E2_7 is not None and 'E2_7' not in already_processed:
            already_processed.append('E2_7')
            showIndent(outfile, level)
            outfile.write('E2_7 = %s,\n' % (self.E2_7,))
        if self.E2_130 is not None and 'E2_130' not in already_processed:
            already_processed.append('E2_130')
            showIndent(outfile, level)
            outfile.write('E2_130 = %s,\n' % (self.E2_130,))
        if self.E2_41 is not None and 'E2_41' not in already_processed:
            already_processed.append('E2_41')
            showIndent(outfile, level)
            outfile.write('E2_41 = %s,\n' % (self.E2_41,))
        if self.E2_42 is not None and 'E2_42' not in already_processed:
            already_processed.append('E2_42')
            showIndent(outfile, level)
            outfile.write('E2_42 = %s,\n' % (self.E2_42,))
        if self.E2_44 is not None and 'E2_44' not in already_processed:
            already_processed.append('E2_44')
            showIndent(outfile, level)
            outfile.write('E2_44 = %s,\n' % (self.E2_44,))
        if self.E2_46 is not None and 'E2_46' not in already_processed:
            already_processed.append('E2_46')
            showIndent(outfile, level)
            outfile.write('E2_46 = %s,\n' % (self.E2_46,))
        if self.E2_66 is not None and 'E2_66' not in already_processed:
            already_processed.append('E2_66')
            showIndent(outfile, level)
            outfile.write('E2_66 = %s,\n' % (self.E2_66,))
        if self.E2_34 is not None and 'E2_34' not in already_processed:
            already_processed.append('E2_34')
            showIndent(outfile, level)
            outfile.write('E2_34 = %s,\n' % (self.E2_34,))
        if self.E2_22 is not None and 'E2_22' not in already_processed:
            already_processed.append('E2_22')
            showIndent(outfile, level)
            outfile.write('E2_22 = %s,\n' % (self.E2_22,))
        if self.E2_21 is not None and 'E2_21' not in already_processed:
            already_processed.append('E2_21')
            showIndent(outfile, level)
            outfile.write('E2_21 = %s,\n' % (self.E2_21,))
        if self.E2_26 is not None and 'E2_26' not in already_processed:
            already_processed.append('E2_26')
            showIndent(outfile, level)
            outfile.write('E2_26 = %s,\n' % (self.E2_26,))
        if self.E2_24 is not None and 'E2_24' not in already_processed:
            already_processed.append('E2_24')
            showIndent(outfile, level)
            outfile.write('E2_24 = %s,\n' % (self.E2_24,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('E2_32')
        if value is not None and 'E2_32' not in already_processed:
            already_processed.append('E2_32')
            self.E2_32 = value
        value = attrs.get('E2_120')
        if value is not None and 'E2_120' not in already_processed:
            already_processed.append('E2_120')
            self.E2_120 = value
        value = attrs.get('E2_52')
        if value is not None and 'E2_52' not in already_processed:
            already_processed.append('E2_52')
            self.E2_52 = value
        value = attrs.get('E2_36')
        if value is not None and 'E2_36' not in already_processed:
            already_processed.append('E2_36')
            self.E2_36 = value
        value = attrs.get('E2_51')
        if value is not None and 'E2_51' not in already_processed:
            already_processed.append('E2_51')
            self.E2_51 = value
        value = attrs.get('E2_56')
        if value is not None and 'E2_56' not in already_processed:
            already_processed.append('E2_56')
            self.E2_56 = value
        value = attrs.get('E2_31')
        if value is not None and 'E2_31' not in already_processed:
            already_processed.append('E2_31')
            self.E2_31 = value
        value = attrs.get('E2_54')
        if value is not None and 'E2_54' not in already_processed:
            already_processed.append('E2_54')
            self.E2_54 = value
        value = attrs.get('E2_16')
        if value is not None and 'E2_16' not in already_processed:
            already_processed.append('E2_16')
            self.E2_16 = value
        value = attrs.get('E2_14')
        if value is not None and 'E2_14' not in already_processed:
            already_processed.append('E2_14')
            self.E2_14 = value
        value = attrs.get('E2_12')
        if value is not None and 'E2_12' not in already_processed:
            already_processed.append('E2_12')
            self.E2_12 = value
        value = attrs.get('E2_10')
        if value is not None and 'E2_10' not in already_processed:
            already_processed.append('E2_10')
            self.E2_10 = value
        value = attrs.get('E2_11')
        if value is not None and 'E2_11' not in already_processed:
            already_processed.append('E2_11')
            self.E2_11 = value
        value = attrs.get('E2_8')
        if value is not None and 'E2_8' not in already_processed:
            already_processed.append('E2_8')
            self.E2_8 = value
        value = attrs.get('E2_9')
        if value is not None and 'E2_9' not in already_processed:
            already_processed.append('E2_9')
            self.E2_9 = value
        value = attrs.get('E2_110')
        if value is not None and 'E2_110' not in already_processed:
            already_processed.append('E2_110')
            self.E2_110 = value
        value = attrs.get('E2_7')
        if value is not None and 'E2_7' not in already_processed:
            already_processed.append('E2_7')
            self.E2_7 = value
        value = attrs.get('E2_130')
        if value is not None and 'E2_130' not in already_processed:
            already_processed.append('E2_130')
            self.E2_130 = value
        value = attrs.get('E2_41')
        if value is not None and 'E2_41' not in already_processed:
            already_processed.append('E2_41')
            self.E2_41 = value
        value = attrs.get('E2_42')
        if value is not None and 'E2_42' not in already_processed:
            already_processed.append('E2_42')
            self.E2_42 = value
        value = attrs.get('E2_44')
        if value is not None and 'E2_44' not in already_processed:
            already_processed.append('E2_44')
            self.E2_44 = value
        value = attrs.get('E2_46')
        if value is not None and 'E2_46' not in already_processed:
            already_processed.append('E2_46')
            self.E2_46 = value
        value = attrs.get('E2_66')
        if value is not None and 'E2_66' not in already_processed:
            already_processed.append('E2_66')
            self.E2_66 = value
        value = attrs.get('E2_34')
        if value is not None and 'E2_34' not in already_processed:
            already_processed.append('E2_34')
            self.E2_34 = value
        value = attrs.get('E2_22')
        if value is not None and 'E2_22' not in already_processed:
            already_processed.append('E2_22')
            self.E2_22 = value
        value = attrs.get('E2_21')
        if value is not None and 'E2_21' not in already_processed:
            already_processed.append('E2_21')
            self.E2_21 = value
        value = attrs.get('E2_26')
        if value is not None and 'E2_26' not in already_processed:
            already_processed.append('E2_26')
            self.E2_26 = value
        value = attrs.get('E2_24')
        if value is not None and 'E2_24' not in already_processed:
            already_processed.append('E2_24')
            self.E2_24 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorE2Type


class AngajatorE3Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, E3_33=None, E3_14=None, E3_31=None, E3_41=None, E3_11=None, E3_13=None, E3_12=None, E3_24=None, E3_43=None, E3_suma=None, E3_34=None, E3_21=None, E3_22=None, E3_23=None, E3_42=None, E3_total=None, E3_32=None, E3_44=None, valueOf_=None):
        self.E3_33 = _cast(None, E3_33)
        self.E3_14 = _cast(None, E3_14)
        self.E3_31 = _cast(None, E3_31)
        self.E3_41 = _cast(None, E3_41)
        self.E3_11 = _cast(None, E3_11)
        self.E3_13 = _cast(None, E3_13)
        self.E3_12 = _cast(None, E3_12)
        self.E3_24 = _cast(None, E3_24)
        self.E3_43 = _cast(None, E3_43)
        self.E3_suma = _cast(None, E3_suma)
        self.E3_34 = _cast(None, E3_34)
        self.E3_21 = _cast(None, E3_21)
        self.E3_22 = _cast(None, E3_22)
        self.E3_23 = _cast(None, E3_23)
        self.E3_42 = _cast(None, E3_42)
        self.E3_total = _cast(None, E3_total)
        self.E3_32 = _cast(None, E3_32)
        self.E3_44 = _cast(None, E3_44)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorE3Type.subclass:
            return AngajatorE3Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorE3Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_E3_33(self): return self.E3_33
    def set_E3_33(self, E3_33): self.E3_33 = E3_33
    def get_E3_14(self): return self.E3_14
    def set_E3_14(self, E3_14): self.E3_14 = E3_14
    def get_E3_31(self): return self.E3_31
    def set_E3_31(self, E3_31): self.E3_31 = E3_31
    def get_E3_41(self): return self.E3_41
    def set_E3_41(self, E3_41): self.E3_41 = E3_41
    def get_E3_11(self): return self.E3_11
    def set_E3_11(self, E3_11): self.E3_11 = E3_11
    def get_E3_13(self): return self.E3_13
    def set_E3_13(self, E3_13): self.E3_13 = E3_13
    def get_E3_12(self): return self.E3_12
    def set_E3_12(self, E3_12): self.E3_12 = E3_12
    def get_E3_24(self): return self.E3_24
    def set_E3_24(self, E3_24): self.E3_24 = E3_24
    def get_E3_43(self): return self.E3_43
    def set_E3_43(self, E3_43): self.E3_43 = E3_43
    def get_E3_suma(self): return self.E3_suma
    def set_E3_suma(self, E3_suma): self.E3_suma = E3_suma
    def get_E3_34(self): return self.E3_34
    def set_E3_34(self, E3_34): self.E3_34 = E3_34
    def get_E3_21(self): return self.E3_21
    def set_E3_21(self, E3_21): self.E3_21 = E3_21
    def get_E3_22(self): return self.E3_22
    def set_E3_22(self, E3_22): self.E3_22 = E3_22
    def get_E3_23(self): return self.E3_23
    def set_E3_23(self, E3_23): self.E3_23 = E3_23
    def get_E3_42(self): return self.E3_42
    def set_E3_42(self, E3_42): self.E3_42 = E3_42
    def get_E3_total(self): return self.E3_total
    def set_E3_total(self, E3_total): self.E3_total = E3_total
    def get_E3_32(self): return self.E3_32
    def set_E3_32(self, E3_32): self.E3_32 = E3_32
    def get_E3_44(self): return self.E3_44
    def set_E3_44(self, E3_44): self.E3_44 = E3_44
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorE3Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorE3Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorE3Type'):
        if self.E3_33 is not None and 'E3_33' not in already_processed:
            already_processed.append('E3_33')
            outfile.write(' E3_33=%s' % (quote_attrib(self.E3_33), ))
        if self.E3_14 is not None and 'E3_14' not in already_processed:
            already_processed.append('E3_14')
            outfile.write(' E3_14=%s' % (quote_attrib(self.E3_14), ))
        if self.E3_31 is not None and 'E3_31' not in already_processed:
            already_processed.append('E3_31')
            outfile.write(' E3_31=%s' % (quote_attrib(self.E3_31), ))
        if self.E3_41 is not None and 'E3_41' not in already_processed:
            already_processed.append('E3_41')
            outfile.write(' E3_41=%s' % (quote_attrib(self.E3_41), ))
        if self.E3_11 is not None and 'E3_11' not in already_processed:
            already_processed.append('E3_11')
            outfile.write(' E3_11=%s' % (quote_attrib(self.E3_11), ))
        if self.E3_13 is not None and 'E3_13' not in already_processed:
            already_processed.append('E3_13')
            outfile.write(' E3_13=%s' % (quote_attrib(self.E3_13), ))
        if self.E3_12 is not None and 'E3_12' not in already_processed:
            already_processed.append('E3_12')
            outfile.write(' E3_12=%s' % (quote_attrib(self.E3_12), ))
        if self.E3_24 is not None and 'E3_24' not in already_processed:
            already_processed.append('E3_24')
            outfile.write(' E3_24=%s' % (quote_attrib(self.E3_24), ))
        if self.E3_43 is not None and 'E3_43' not in already_processed:
            already_processed.append('E3_43')
            outfile.write(' E3_43=%s' % (quote_attrib(self.E3_43), ))
        if self.E3_suma is not None and 'E3_suma' not in already_processed:
            already_processed.append('E3_suma')
            outfile.write(' E3_suma=%s' % (quote_attrib(self.E3_suma), ))
        if self.E3_34 is not None and 'E3_34' not in already_processed:
            already_processed.append('E3_34')
            outfile.write(' E3_34=%s' % (quote_attrib(self.E3_34), ))
        if self.E3_21 is not None and 'E3_21' not in already_processed:
            already_processed.append('E3_21')
            outfile.write(' E3_21=%s' % (quote_attrib(self.E3_21), ))
        if self.E3_22 is not None and 'E3_22' not in already_processed:
            already_processed.append('E3_22')
            outfile.write(' E3_22=%s' % (quote_attrib(self.E3_22), ))
        if self.E3_23 is not None and 'E3_23' not in already_processed:
            already_processed.append('E3_23')
            outfile.write(' E3_23=%s' % (quote_attrib(self.E3_23), ))
        if self.E3_42 is not None and 'E3_42' not in already_processed:
            already_processed.append('E3_42')
            outfile.write(' E3_42=%s' % (quote_attrib(self.E3_42), ))
        if self.E3_total is not None and 'E3_total' not in already_processed:
            already_processed.append('E3_total')
            outfile.write(' E3_total=%s' % (quote_attrib(self.E3_total), ))
        if self.E3_32 is not None and 'E3_32' not in already_processed:
            already_processed.append('E3_32')
            outfile.write(' E3_32=%s' % (quote_attrib(self.E3_32), ))
        if self.E3_44 is not None and 'E3_44' not in already_processed:
            already_processed.append('E3_44')
            outfile.write(' E3_44=%s' % (quote_attrib(self.E3_44), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorE3Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorE3Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.E3_33 is not None and 'E3_33' not in already_processed:
            already_processed.append('E3_33')
            showIndent(outfile, level)
            outfile.write('E3_33 = %s,\n' % (self.E3_33,))
        if self.E3_14 is not None and 'E3_14' not in already_processed:
            already_processed.append('E3_14')
            showIndent(outfile, level)
            outfile.write('E3_14 = %s,\n' % (self.E3_14,))
        if self.E3_31 is not None and 'E3_31' not in already_processed:
            already_processed.append('E3_31')
            showIndent(outfile, level)
            outfile.write('E3_31 = %s,\n' % (self.E3_31,))
        if self.E3_41 is not None and 'E3_41' not in already_processed:
            already_processed.append('E3_41')
            showIndent(outfile, level)
            outfile.write('E3_41 = %s,\n' % (self.E3_41,))
        if self.E3_11 is not None and 'E3_11' not in already_processed:
            already_processed.append('E3_11')
            showIndent(outfile, level)
            outfile.write('E3_11 = %s,\n' % (self.E3_11,))
        if self.E3_13 is not None and 'E3_13' not in already_processed:
            already_processed.append('E3_13')
            showIndent(outfile, level)
            outfile.write('E3_13 = %s,\n' % (self.E3_13,))
        if self.E3_12 is not None and 'E3_12' not in already_processed:
            already_processed.append('E3_12')
            showIndent(outfile, level)
            outfile.write('E3_12 = %s,\n' % (self.E3_12,))
        if self.E3_24 is not None and 'E3_24' not in already_processed:
            already_processed.append('E3_24')
            showIndent(outfile, level)
            outfile.write('E3_24 = %s,\n' % (self.E3_24,))
        if self.E3_43 is not None and 'E3_43' not in already_processed:
            already_processed.append('E3_43')
            showIndent(outfile, level)
            outfile.write('E3_43 = %s,\n' % (self.E3_43,))
        if self.E3_suma is not None and 'E3_suma' not in already_processed:
            already_processed.append('E3_suma')
            showIndent(outfile, level)
            outfile.write('E3_suma = %s,\n' % (self.E3_suma,))
        if self.E3_34 is not None and 'E3_34' not in already_processed:
            already_processed.append('E3_34')
            showIndent(outfile, level)
            outfile.write('E3_34 = %s,\n' % (self.E3_34,))
        if self.E3_21 is not None and 'E3_21' not in already_processed:
            already_processed.append('E3_21')
            showIndent(outfile, level)
            outfile.write('E3_21 = %s,\n' % (self.E3_21,))
        if self.E3_22 is not None and 'E3_22' not in already_processed:
            already_processed.append('E3_22')
            showIndent(outfile, level)
            outfile.write('E3_22 = %s,\n' % (self.E3_22,))
        if self.E3_23 is not None and 'E3_23' not in already_processed:
            already_processed.append('E3_23')
            showIndent(outfile, level)
            outfile.write('E3_23 = %s,\n' % (self.E3_23,))
        if self.E3_42 is not None and 'E3_42' not in already_processed:
            already_processed.append('E3_42')
            showIndent(outfile, level)
            outfile.write('E3_42 = %s,\n' % (self.E3_42,))
        if self.E3_total is not None and 'E3_total' not in already_processed:
            already_processed.append('E3_total')
            showIndent(outfile, level)
            outfile.write('E3_total = %s,\n' % (self.E3_total,))
        if self.E3_32 is not None and 'E3_32' not in already_processed:
            already_processed.append('E3_32')
            showIndent(outfile, level)
            outfile.write('E3_32 = %s,\n' % (self.E3_32,))
        if self.E3_44 is not None and 'E3_44' not in already_processed:
            already_processed.append('E3_44')
            showIndent(outfile, level)
            outfile.write('E3_44 = %s,\n' % (self.E3_44,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('E3_33')
        if value is not None and 'E3_33' not in already_processed:
            already_processed.append('E3_33')
            self.E3_33 = value
        value = attrs.get('E3_14')
        if value is not None and 'E3_14' not in already_processed:
            already_processed.append('E3_14')
            self.E3_14 = value
        value = attrs.get('E3_31')
        if value is not None and 'E3_31' not in already_processed:
            already_processed.append('E3_31')
            self.E3_31 = value
        value = attrs.get('E3_41')
        if value is not None and 'E3_41' not in already_processed:
            already_processed.append('E3_41')
            self.E3_41 = value
        value = attrs.get('E3_11')
        if value is not None and 'E3_11' not in already_processed:
            already_processed.append('E3_11')
            self.E3_11 = value
        value = attrs.get('E3_13')
        if value is not None and 'E3_13' not in already_processed:
            already_processed.append('E3_13')
            self.E3_13 = value
        value = attrs.get('E3_12')
        if value is not None and 'E3_12' not in already_processed:
            already_processed.append('E3_12')
            self.E3_12 = value
        value = attrs.get('E3_24')
        if value is not None and 'E3_24' not in already_processed:
            already_processed.append('E3_24')
            self.E3_24 = value
        value = attrs.get('E3_43')
        if value is not None and 'E3_43' not in already_processed:
            already_processed.append('E3_43')
            self.E3_43 = value
        value = attrs.get('E3_suma')
        if value is not None and 'E3_suma' not in already_processed:
            already_processed.append('E3_suma')
            self.E3_suma = value
        value = attrs.get('E3_34')
        if value is not None and 'E3_34' not in already_processed:
            already_processed.append('E3_34')
            self.E3_34 = value
        value = attrs.get('E3_21')
        if value is not None and 'E3_21' not in already_processed:
            already_processed.append('E3_21')
            self.E3_21 = value
        value = attrs.get('E3_22')
        if value is not None and 'E3_22' not in already_processed:
            already_processed.append('E3_22')
            self.E3_22 = value
        value = attrs.get('E3_23')
        if value is not None and 'E3_23' not in already_processed:
            already_processed.append('E3_23')
            self.E3_23 = value
        value = attrs.get('E3_42')
        if value is not None and 'E3_42' not in already_processed:
            already_processed.append('E3_42')
            self.E3_42 = value
        value = attrs.get('E3_total')
        if value is not None and 'E3_total' not in already_processed:
            already_processed.append('E3_total')
            self.E3_total = value
        value = attrs.get('E3_32')
        if value is not None and 'E3_32' not in already_processed:
            already_processed.append('E3_32')
            self.E3_32 = value
        value = attrs.get('E3_44')
        if value is not None and 'E3_44' not in already_processed:
            already_processed.append('E3_44')
            self.E3_44 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorE3Type


class AngajatorE4Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, E4_aj_suma=None, E4_aj_nr=None, valueOf_=None):
        self.E4_aj_suma = _cast(None, E4_aj_suma)
        self.E4_aj_nr = _cast(None, E4_aj_nr)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorE4Type.subclass:
            return AngajatorE4Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorE4Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_E4_aj_suma(self): return self.E4_aj_suma
    def set_E4_aj_suma(self, E4_aj_suma): self.E4_aj_suma = E4_aj_suma
    def get_E4_aj_nr(self): return self.E4_aj_nr
    def set_E4_aj_nr(self, E4_aj_nr): self.E4_aj_nr = E4_aj_nr
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorE4Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorE4Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorE4Type'):
        if self.E4_aj_suma is not None and 'E4_aj_suma' not in already_processed:
            already_processed.append('E4_aj_suma')
            outfile.write(' E4_aj_suma=%s' % (quote_attrib(self.E4_aj_suma), ))
        if self.E4_aj_nr is not None and 'E4_aj_nr' not in already_processed:
            already_processed.append('E4_aj_nr')
            outfile.write(' E4_aj_nr=%s' % (quote_attrib(self.E4_aj_nr), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorE4Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorE4Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.E4_aj_suma is not None and 'E4_aj_suma' not in already_processed:
            already_processed.append('E4_aj_suma')
            showIndent(outfile, level)
            outfile.write('E4_aj_suma = %s,\n' % (self.E4_aj_suma,))
        if self.E4_aj_nr is not None and 'E4_aj_nr' not in already_processed:
            already_processed.append('E4_aj_nr')
            showIndent(outfile, level)
            outfile.write('E4_aj_nr = %s,\n' % (self.E4_aj_nr,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('E4_aj_suma')
        if value is not None and 'E4_aj_suma' not in already_processed:
            already_processed.append('E4_aj_suma')
            self.E4_aj_suma = value
        value = attrs.get('E4_aj_nr')
        if value is not None and 'E4_aj_nr' not in already_processed:
            already_processed.append('E4_aj_nr')
            self.E4_aj_nr = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorE4Type


class AngajatorF1Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, F1_suma=None, valueOf_=None):
        self.F1_suma = _cast(None, F1_suma)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorF1Type.subclass:
            return AngajatorF1Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorF1Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_F1_suma(self): return self.F1_suma
    def set_F1_suma(self, F1_suma): self.F1_suma = F1_suma
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorF1Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorF1Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorF1Type'):
        if self.F1_suma is not None and 'F1_suma' not in already_processed:
            already_processed.append('F1_suma')
            outfile.write(' F1_suma=%s' % (quote_attrib(self.F1_suma), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorF1Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorF1Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.F1_suma is not None and 'F1_suma' not in already_processed:
            already_processed.append('F1_suma')
            showIndent(outfile, level)
            outfile.write('F1_suma = %s,\n' % (self.F1_suma,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('F1_suma')
        if value is not None and 'F1_suma' not in already_processed:
            already_processed.append('F1_suma')
            self.F1_suma = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorF1Type


class AngajatorF2Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, F2_cif=None, F2_id=None, F2_suma=None, valueOf_=None):
        self.F2_cif = _cast(None, F2_cif)
        self.F2_id = _cast(None, F2_id)
        self.F2_suma = _cast(None, F2_suma)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AngajatorF2Type.subclass:
            return AngajatorF2Type.subclass(*args_, **kwargs_)
        else:
            return AngajatorF2Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_F2_cif(self): return self.F2_cif
    def set_F2_cif(self, F2_cif): self.F2_cif = F2_cif
    def get_F2_id(self): return self.F2_id
    def set_F2_id(self, F2_id): self.F2_id = F2_id
    def get_F2_suma(self): return self.F2_suma
    def set_F2_suma(self, F2_suma): self.F2_suma = F2_suma
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AngajatorF2Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AngajatorF2Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AngajatorF2Type'):
        outfile.write(' F2_cif=%s' % (quote_attrib(self.F2_cif), ))
        outfile.write(' F2_id=%s' % (quote_attrib(self.F2_id), ))
        outfile.write(' F2_suma=%s' % (quote_attrib(self.F2_suma), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AngajatorF2Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AngajatorF2Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.F2_cif is not None and 'F2_cif' not in already_processed:
            already_processed.append('F2_cif')
            showIndent(outfile, level)
            outfile.write('F2_cif = %s,\n' % (self.F2_cif,))
        if self.F2_id is not None and 'F2_id' not in already_processed:
            already_processed.append('F2_id')
            showIndent(outfile, level)
            outfile.write('F2_id = %s,\n' % (self.F2_id,))
        if self.F2_suma is not None and 'F2_suma' not in already_processed:
            already_processed.append('F2_suma')
            showIndent(outfile, level)
            outfile.write('F2_suma = %s,\n' % (self.F2_suma,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('F2_cif')
        if value is not None and 'F2_cif' not in already_processed:
            already_processed.append('F2_cif')
            self.F2_cif = value
        value = attrs.get('F2_id')
        if value is not None and 'F2_id' not in already_processed:
            already_processed.append('F2_id')
            self.F2_id = value
        value = attrs.get('F2_suma')
        if value is not None and 'F2_suma' not in already_processed:
            already_processed.append('F2_suma')
            self.F2_suma = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AngajatorF2Type


class AsiguratType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, prenAsig=None, prenAnt=None, cnpAsig=None, casaSn=None, asigSO=None, numeAnt=None, dataSf=None, idAsig=None, numeAsig=None, asigCI=None, cnpAnt=None, dataAng=None, coAsigurati=None, asiguratA=None, asiguratC=None, asiguratD=None, asiguratB1=None, asiguratB2=None, asiguratB3=None, asiguratB4=None):
        self.prenAsig = _cast(None, prenAsig)
        self.prenAnt = _cast(None, prenAnt)
        self.cnpAsig = _cast(None, cnpAsig)
        self.casaSn = _cast(None, casaSn)
        self.asigSO = _cast(int, asigSO)
        self.numeAnt = _cast(None, numeAnt)
        self.dataSf = _cast(None, dataSf)
        self.idAsig = _cast(None, idAsig)
        self.numeAsig = _cast(None, numeAsig)
        self.asigCI = _cast(int, asigCI)
        self.cnpAnt = _cast(None, cnpAnt)
        self.dataAng = _cast(None, dataAng)
        if coAsigurati is None:
            self.coAsigurati = []
        else:
            self.coAsigurati = coAsigurati
        self.asiguratA = asiguratA
        self.asiguratC = asiguratC
        if asiguratD is None:
            self.asiguratD = []
        else:
            self.asiguratD = asiguratD
        if asiguratB1 is None:
            self.asiguratB1 = []
        else:
            self.asiguratB1 = asiguratB1
        self.asiguratB2 = asiguratB2
        self.asiguratB3 = asiguratB3
        self.asiguratB4 = asiguratB4
    def factory(*args_, **kwargs_):
        if AsiguratType.subclass:
            return AsiguratType.subclass(*args_, **kwargs_)
        else:
            return AsiguratType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_coAsigurati(self): return self.coAsigurati
    def set_coAsigurati(self, coAsigurati): self.coAsigurati = coAsigurati
    def add_coAsigurati(self, value): self.coAsigurati.append(value)
    def insert_coAsigurati(self, index, value): self.coAsigurati[index] = value
    def get_asiguratA(self): return self.asiguratA
    def set_asiguratA(self, asiguratA): self.asiguratA = asiguratA
    def get_asiguratC(self): return self.asiguratC
    def set_asiguratC(self, asiguratC): self.asiguratC = asiguratC
    def get_asiguratD(self): return self.asiguratD
    def set_asiguratD(self, asiguratD): self.asiguratD = asiguratD
    def add_asiguratD(self, value): self.asiguratD.append(value)
    def insert_asiguratD(self, index, value): self.asiguratD[index] = value
    def get_asiguratB1(self): return self.asiguratB1
    def set_asiguratB1(self, asiguratB1): self.asiguratB1 = asiguratB1
    def add_asiguratB1(self, value): self.asiguratB1.append(value)
    def insert_asiguratB1(self, index, value): self.asiguratB1[index] = value
    def get_asiguratB2(self): return self.asiguratB2
    def set_asiguratB2(self, asiguratB2): self.asiguratB2 = asiguratB2
    def get_asiguratB3(self): return self.asiguratB3
    def set_asiguratB3(self, asiguratB3): self.asiguratB3 = asiguratB3
    def get_asiguratB4(self): return self.asiguratB4
    def set_asiguratB4(self, asiguratB4): self.asiguratB4 = asiguratB4
    def get_asiguratC(self): return self.asiguratC
    def set_asiguratC(self, asiguratC): self.asiguratC = asiguratC
    def get_asiguratC(self): return self.asiguratC
    def set_asiguratC(self, asiguratC): self.asiguratC = asiguratC
    def get_prenAsig(self): return self.prenAsig
    def set_prenAsig(self, prenAsig): self.prenAsig = prenAsig
    def get_prenAnt(self): return self.prenAnt
    def set_prenAnt(self, prenAnt): self.prenAnt = prenAnt
    def get_cnpAsig(self): return self.cnpAsig
    def set_cnpAsig(self, cnpAsig): self.cnpAsig = cnpAsig
    def get_casaSn(self): return self.casaSn
    def set_casaSn(self, casaSn): self.casaSn = casaSn
    def get_asigSO(self): return self.asigSO
    def set_asigSO(self, asigSO): self.asigSO = asigSO
    def get_numeAnt(self): return self.numeAnt
    def set_numeAnt(self, numeAnt): self.numeAnt = numeAnt
    def get_dataSf(self): return self.dataSf
    def set_dataSf(self, dataSf): self.dataSf = dataSf
    def get_idAsig(self): return self.idAsig
    def set_idAsig(self, idAsig): self.idAsig = idAsig
    def get_numeAsig(self): return self.numeAsig
    def set_numeAsig(self, numeAsig): self.numeAsig = numeAsig
    def get_asigCI(self): return self.asigCI
    def set_asigCI(self, asigCI): self.asigCI = asigCI
    def get_cnpAnt(self): return self.cnpAnt
    def set_cnpAnt(self, cnpAnt): self.cnpAnt = cnpAnt
    def get_dataAng(self): return self.dataAng
    def set_dataAng(self, dataAng): self.dataAng = dataAng
    def export(self, outfile, level, namespace_='', name_='AsiguratType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratType')
        if self.hasContent_():
            outfile.write('>\n')
            self.exportChildren(outfile, level + 1, namespace_, name_)
            showIndent(outfile, level)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratType'):
        if self.prenAsig is not None and 'prenAsig' not in already_processed:
            already_processed.append('prenAsig')
            outfile.write(' prenAsig=%s' % (self.gds_format_string(quote_attrib(self.prenAsig).encode(ExternalEncoding), input_name='prenAsig'), ))
        if self.prenAnt is not None and 'prenAnt' not in already_processed:
            already_processed.append('prenAnt')
            outfile.write(' prenAnt=%s' % (self.gds_format_string(quote_attrib(self.prenAnt).encode(ExternalEncoding), input_name='prenAnt'), ))
        outfile.write(' cnpAsig=%s' % (quote_attrib(self.cnpAsig), ))
        if self.casaSn is not None and 'casaSn' not in already_processed:
            already_processed.append('casaSn')
            outfile.write(' casaSn=%s' % (quote_attrib(self.casaSn), ))
        outfile.write(' asigSO="%s"' % self.gds_format_integer(self.asigSO, input_name='asigSO'))
        if self.numeAnt is not None and 'numeAnt' not in already_processed:
            already_processed.append('numeAnt')
            outfile.write(' numeAnt=%s' % (self.gds_format_string(quote_attrib(self.numeAnt).encode(ExternalEncoding), input_name='numeAnt'), ))
        if self.dataSf is not None and 'dataSf' not in already_processed:
            already_processed.append('dataSf')
            outfile.write(' dataSf=%s' % (quote_attrib(self.dataSf), ))
        outfile.write(' idAsig=%s' % (quote_attrib(self.idAsig), ))
        if self.numeAsig is not None and 'numeAsig' not in already_processed:
            already_processed.append('numeAsig')
            outfile.write(' numeAsig=%s' % (self.gds_format_string(quote_attrib(self.numeAsig).encode(ExternalEncoding), input_name='numeAsig'), ))
        outfile.write(' asigCI="%s"' % self.gds_format_integer(self.asigCI, input_name='asigCI'))
        if self.cnpAnt is not None and 'cnpAnt' not in already_processed:
            already_processed.append('cnpAnt')
            outfile.write(' cnpAnt=%s' % (quote_attrib(self.cnpAnt), ))
        if self.dataAng is not None and 'dataAng' not in already_processed:
            already_processed.append('dataAng')
            outfile.write(' dataAng=%s' % (quote_attrib(self.dataAng), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratType'):
        for coAsigurati_ in self.coAsigurati:
            coAsigurati_.export(outfile, level, namespace_, name_='coAsigurati')
        if self.asiguratA:
            self.asiguratA.export(outfile, level, namespace_, name_='asiguratA', )
        if self.asiguratC:
            self.asiguratC.export(outfile, level, namespace_, name_='asiguratC', )
        for asiguratB1_ in self.asiguratB1:
            asiguratB1_.export(outfile, level, namespace_, name_='asiguratB1')
        if self.asiguratB2:
            self.asiguratB2.export(outfile, level, namespace_, name_='asiguratB2')
        if self.asiguratB3:
            self.asiguratB3.export(outfile, level, namespace_, name_='asiguratB3')
        if self.asiguratB4:
            self.asiguratB4.export(outfile, level, namespace_, name_='asiguratB4', )
        for asiguratD_ in self.asiguratD:
	        asiguratD_.export(outfile, level, namespace_, name_='asiguratD')			
    def hasContent_(self):
        if (
            self.coAsigurati or
            self.asiguratA is not None or
            self.asiguratC is not None or
            self.asiguratD or
            self.asiguratB1 or
            self.asiguratB2 is not None or
            self.asiguratB3 is not None or
            self.asiguratB4 is not None
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.prenAsig is not None and 'prenAsig' not in already_processed:
            already_processed.append('prenAsig')
            showIndent(outfile, level)
            outfile.write('prenAsig = "%s",\n' % (self.prenAsig,))
        if self.prenAnt is not None and 'prenAnt' not in already_processed:
            already_processed.append('prenAnt')
            showIndent(outfile, level)
            outfile.write('prenAnt = "%s",\n' % (self.prenAnt,))
        if self.cnpAsig is not None and 'cnpAsig' not in already_processed:
            already_processed.append('cnpAsig')
            showIndent(outfile, level)
            outfile.write('cnpAsig = %s,\n' % (self.cnpAsig,))
        if self.casaSn is not None and 'casaSn' not in already_processed:
            already_processed.append('casaSn')
            showIndent(outfile, level)
            outfile.write('casaSn = %s,\n' % (self.casaSn,))
        if self.asigSO is not None and 'asigSO' not in already_processed:
            already_processed.append('asigSO')
            showIndent(outfile, level)
            outfile.write('asigSO = %d,\n' % (self.asigSO,))
        if self.numeAnt is not None and 'numeAnt' not in already_processed:
            already_processed.append('numeAnt')
            showIndent(outfile, level)
            outfile.write('numeAnt = "%s",\n' % (self.numeAnt,))
        if self.dataSf is not None and 'dataSf' not in already_processed:
            already_processed.append('dataSf')
            showIndent(outfile, level)
            outfile.write('dataSf = %s,\n' % (self.dataSf,))
        if self.idAsig is not None and 'idAsig' not in already_processed:
            already_processed.append('idAsig')
            showIndent(outfile, level)
            outfile.write('idAsig = %s,\n' % (self.idAsig,))
        if self.numeAsig is not None and 'numeAsig' not in already_processed:
            already_processed.append('numeAsig')
            showIndent(outfile, level)
            outfile.write('numeAsig = "%s",\n' % (self.numeAsig,))
        if self.asigCI is not None and 'asigCI' not in already_processed:
            already_processed.append('asigCI')
            showIndent(outfile, level)
            outfile.write('asigCI = %d,\n' % (self.asigCI,))
        if self.cnpAnt is not None and 'cnpAnt' not in already_processed:
            already_processed.append('cnpAnt')
            showIndent(outfile, level)
            outfile.write('cnpAnt = %s,\n' % (self.cnpAnt,))
        if self.dataAng is not None and 'dataAng' not in already_processed:
            already_processed.append('dataAng')
            showIndent(outfile, level)
            outfile.write('dataAng = %s,\n' % (self.dataAng,))
    def exportLiteralChildren(self, outfile, level, name_):
        showIndent(outfile, level)
        outfile.write('coAsigurati=[\n')
        level += 1
        for coAsigurati_ in self.coAsigurati:
            showIndent(outfile, level)
            outfile.write('model_.CoAsiguratiType(\n')
            coAsigurati_.exportLiteral(outfile, level, name_='CoAsiguratiType')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
        if self.asiguratA is not None:
            showIndent(outfile, level)
            outfile.write('asiguratA=model_.AsiguratAType(\n')
            self.asiguratA.exportLiteral(outfile, level, name_='asiguratA')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.asiguratC is not None:
            showIndent(outfile, level)
            outfile.write('asiguratC=model_.AsiguratCType(\n')
            self.asiguratC.exportLiteral(outfile, level, name_='asiguratC')
            showIndent(outfile, level)
            outfile.write('),\n')
        showIndent(outfile, level)
        outfile.write('asiguratD=[\n')
        level += 1
        for asiguratD_ in self.asiguratD:
            showIndent(outfile, level)
            outfile.write('model_.AsiguratDType(\n')
            asiguratD_.exportLiteral(outfile, level, name_='AsiguratDType')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
        showIndent(outfile, level)
        outfile.write('asiguratB1=[\n')
        level += 1
        for asiguratB1_ in self.asiguratB1:
            showIndent(outfile, level)
            outfile.write('model_.AsiguratB1Type(\n')
            asiguratB1_.exportLiteral(outfile, level, name_='AsiguratB1Type')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
        if self.asiguratB2 is not None:
            showIndent(outfile, level)
            outfile.write('asiguratB2=model_.AsiguratB2Type(\n')
            self.asiguratB2.exportLiteral(outfile, level, name_='asiguratB2')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.asiguratB3 is not None:
            showIndent(outfile, level)
            outfile.write('asiguratB3=model_.AsiguratB3Type(\n')
            self.asiguratB3.exportLiteral(outfile, level, name_='asiguratB3')
            showIndent(outfile, level)
            outfile.write('),\n')
        if self.asiguratB4 is not None:
            showIndent(outfile, level)
            outfile.write('asiguratB4=model_.AsiguratB4Type(\n')
            self.asiguratB4.exportLiteral(outfile, level, name_='asiguratB4')
            showIndent(outfile, level)
            outfile.write('),\n')
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('prenAsig')
        if value is not None and 'prenAsig' not in already_processed:
            already_processed.append('prenAsig')
            self.prenAsig = value
            self.prenAsig = ' '.join(self.prenAsig.split())
        value = attrs.get('prenAnt')
        if value is not None and 'prenAnt' not in already_processed:
            already_processed.append('prenAnt')
            self.prenAnt = value
            self.prenAnt = ' '.join(self.prenAnt.split())
        value = attrs.get('cnpAsig')
        if value is not None and 'cnpAsig' not in already_processed:
            already_processed.append('cnpAsig')
            self.cnpAsig = value
        value = attrs.get('casaSn')
        if value is not None and 'casaSn' not in already_processed:
            already_processed.append('casaSn')
            self.casaSn = value
        value = attrs.get('asigSO')
        if value is not None and 'asigSO' not in already_processed:
            already_processed.append('asigSO')
            try:
                self.asigSO = int(value)
            except ValueError, exp:
                raise_parse_error(node, 'Bad integer attribute: %s' % exp)
        value = attrs.get('numeAnt')
        if value is not None and 'numeAnt' not in already_processed:
            already_processed.append('numeAnt')
            self.numeAnt = value
            self.numeAnt = ' '.join(self.numeAnt.split())
        value = attrs.get('dataSf')
        if value is not None and 'dataSf' not in already_processed:
            already_processed.append('dataSf')
            self.dataSf = value
        value = attrs.get('idAsig')
        if value is not None and 'idAsig' not in already_processed:
            already_processed.append('idAsig')
            self.idAsig = value
        value = attrs.get('numeAsig')
        if value is not None and 'numeAsig' not in already_processed:
            already_processed.append('numeAsig')
            self.numeAsig = value
            self.numeAsig = ' '.join(self.numeAsig.split())
        value = attrs.get('asigCI')
        if value is not None and 'asigCI' not in already_processed:
            already_processed.append('asigCI')
            try:
                self.asigCI = int(value)
            except ValueError, exp:
                raise_parse_error(node, 'Bad integer attribute: %s' % exp)
        value = attrs.get('cnpAnt')
        if value is not None and 'cnpAnt' not in already_processed:
            already_processed.append('cnpAnt')
            self.cnpAnt = value
        value = attrs.get('dataAng')
        if value is not None and 'dataAng' not in already_processed:
            already_processed.append('dataAng')
            self.dataAng = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        if nodeName_ == 'coAsigurati': 
            obj_ = CoAsiguratiType.factory()
            obj_.build(child_)
            self.coAsigurati.append(obj_)
        elif nodeName_ == 'asiguratA': 
            obj_ = AsiguratAType.factory()
            obj_.build(child_)
            self.set_asiguratA(obj_)
        elif nodeName_ == 'asiguratC': 
            obj_ = AsiguratCType.factory()
            obj_.build(child_)
            self.set_asiguratC(obj_)
        elif nodeName_ == 'asiguratD': 
            obj_ = AsiguratDType.factory()
            obj_.build(child_)
            self.asiguratD.append(obj_)
        elif nodeName_ == 'asiguratB1': 
            obj_ = AsiguratB1Type.factory()
            obj_.build(child_)
            self.asiguratB1.append(obj_)
        elif nodeName_ == 'asiguratB2': 
            obj_ = AsiguratB2Type.factory()
            obj_.build(child_)
            self.set_asiguratB2(obj_)
        elif nodeName_ == 'asiguratB3': 
            obj_ = AsiguratB3Type.factory()
            obj_.build(child_)
            self.set_asiguratB3(obj_)
        elif nodeName_ == 'asiguratB4': 
            obj_ = AsiguratB4Type.factory()
            obj_.build(child_)
            self.set_asiguratB4(obj_)
# end class AsiguratType


class CoAsiguratiType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, nume=None, tip=None, prenume=None, cnp=None, valueOf_=None):
        self.nume = _cast(None, nume)
        self.tip = _cast(None, tip)
        self.prenume = _cast(None, prenume)
        self.cnp = _cast(None, cnp)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if CoAsiguratiType.subclass:
            return CoAsiguratiType.subclass(*args_, **kwargs_)
        else:
            return CoAsiguratiType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_nume(self): return self.nume
    def set_nume(self, nume): self.nume = nume
    def get_tip(self): return self.tip
    def set_tip(self, tip): self.tip = tip
    def get_prenume(self): return self.prenume
    def set_prenume(self, prenume): self.prenume = prenume
    def get_cnp(self): return self.cnp
    def set_cnp(self, cnp): self.cnp = cnp
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='CoAsiguratiType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='CoAsiguratiType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='CoAsiguratiType'):
        outfile.write(' nume=%s' % (self.gds_format_string(quote_attrib(self.nume).encode(ExternalEncoding), input_name='nume'), ))
        outfile.write(' tip=%s' % (quote_attrib(self.tip), ))
        outfile.write(' prenume=%s' % (self.gds_format_string(quote_attrib(self.prenume).encode(ExternalEncoding), input_name='prenume'), ))
        outfile.write(' cnp=%s' % (quote_attrib(self.cnp), ))
    def exportChildren(self, outfile, level, namespace_='', name_='CoAsiguratiType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='CoAsiguratiType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.nume is not None and 'nume' not in already_processed:
            already_processed.append('nume')
            showIndent(outfile, level)
            outfile.write('nume = "%s",\n' % (self.nume,))
        if self.tip is not None and 'tip' not in already_processed:
            already_processed.append('tip')
            showIndent(outfile, level)
            outfile.write('tip = %s,\n' % (self.tip,))
        if self.prenume is not None and 'prenume' not in already_processed:
            already_processed.append('prenume')
            showIndent(outfile, level)
            outfile.write('prenume = "%s",\n' % (self.prenume,))
        if self.cnp is not None and 'cnp' not in already_processed:
            already_processed.append('cnp')
            showIndent(outfile, level)
            outfile.write('cnp = %s,\n' % (self.cnp,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('nume')
        if value is not None and 'nume' not in already_processed:
            already_processed.append('nume')
            self.nume = value
            self.nume = ' '.join(self.nume.split())
        value = attrs.get('tip')
        if value is not None and 'tip' not in already_processed:
            already_processed.append('tip')
            self.tip = value
        value = attrs.get('prenume')
        if value is not None and 'prenume' not in already_processed:
            already_processed.append('prenume')
            self.prenume = value
            self.prenume = ' '.join(self.prenume.split())
        value = attrs.get('cnp')
        if value is not None and 'cnp' not in already_processed:
            already_processed.append('cnp')
            self.cnp = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class CoAsiguratiType


class AsiguratAType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, A_7=None, A_6=None, A_5=None, A_4=None, A_3=None, A_2=None, A_1=None, A_9=None, A_8=None, A_20=None, A_13=None, A_12=None, A_11=None, A_10=None, A_14=None, valueOf_=None):
        self.A_7 = _cast(None, A_7)
        self.A_6 = _cast(None, A_6)
        self.A_5 = _cast(None, A_5)
        self.A_4 = _cast(None, A_4)
        self.A_3 = _cast(None, A_3)
        self.A_2 = _cast(None, A_2)
        self.A_1 = _cast(None, A_1)
        self.A_9 = _cast(None, A_9)
        self.A_8 = _cast(None, A_8)
        self.A_20 = _cast(None, A_20)
        self.A_13 = _cast(None, A_13)
        self.A_12 = _cast(None, A_12)
        self.A_11 = _cast(None, A_11)
        self.A_10 = _cast(None, A_10)
        self.A_14 = _cast(None, A_14)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratAType.subclass:
            return AsiguratAType.subclass(*args_, **kwargs_)
        else:
            return AsiguratAType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_A_7(self): return self.A_7
    def set_A_7(self, A_7): self.A_7 = A_7
    def get_A_6(self): return self.A_6
    def set_A_6(self, A_6): self.A_6 = A_6
    def get_A_5(self): return self.A_5
    def set_A_5(self, A_5): self.A_5 = A_5
    def get_A_4(self): return self.A_4
    def set_A_4(self, A_4): self.A_4 = A_4
    def get_A_3(self): return self.A_3
    def set_A_3(self, A_3): self.A_3 = A_3
    def get_A_2(self): return self.A_2
    def set_A_2(self, A_2): self.A_2 = A_2
    def get_A_1(self): return self.A_1
    def set_A_1(self, A_1): self.A_1 = A_1
    def get_A_9(self): return self.A_9
    def set_A_9(self, A_9): self.A_9 = A_9
    def get_A_8(self): return self.A_8
    def set_A_8(self, A_8): self.A_8 = A_8
    def get_A_20(self): return self.A_20
    def set_A_20(self, A_20): self.A_20 = A_20
    def get_A_13(self): return self.A_13
    def set_A_13(self, A_13): self.A_13 = A_13
    def get_A_12(self): return self.A_12
    def set_A_12(self, A_12): self.A_12 = A_12
    def get_A_11(self): return self.A_11
    def set_A_11(self, A_11): self.A_11 = A_11
    def get_A_10(self): return self.A_10
    def set_A_10(self, A_10): self.A_10 = A_10
    def get_A_14(self): return self.A_14
    def set_A_14(self, A_14): self.A_14 = A_14
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratAType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratAType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratAType'):
        if self.A_7 is not None and 'A_7' not in already_processed:
            already_processed.append('A_7')
            outfile.write(' A_7=%s' % (quote_attrib(self.A_7), ))
        if self.A_6 is not None and 'A_6' not in already_processed:
            already_processed.append('A_6')
            outfile.write(' A_6=%s' % (quote_attrib(self.A_6), ))
        if self.A_5 is not None and 'A_5' not in already_processed:
            already_processed.append('A_5')
            outfile.write(' A_5=%s' % (quote_attrib(self.A_5), ))
        outfile.write(' A_4=%s' % (quote_attrib(self.A_4), ))
        outfile.write(' A_3=%s' % (quote_attrib(self.A_3), ))
        outfile.write(' A_2=%s' % (quote_attrib(self.A_2), ))
        outfile.write(' A_1=%s' % (quote_attrib(self.A_1), ))
        if self.A_9 is not None and 'A_9' not in already_processed:
            already_processed.append('A_9')
            outfile.write(' A_9=%s' % (quote_attrib(self.A_9), ))
        if self.A_8 is not None and 'A_8' not in already_processed:
            already_processed.append('A_8')
            outfile.write(' A_8=%s' % (quote_attrib(self.A_8), ))
        outfile.write(' A_20=%s' % (quote_attrib(self.A_20), ))
        outfile.write(' A_13=%s' % (quote_attrib(self.A_13), ))
        outfile.write(' A_12=%s' % (quote_attrib(self.A_12), ))
        outfile.write(' A_11=%s' % (quote_attrib(self.A_11), ))
        if self.A_10 is not None and 'A_10' not in already_processed:
            already_processed.append('A_10')
            outfile.write(' A_10=%s' % (quote_attrib(self.A_10), ))
        outfile.write(' A_14=%s' % (quote_attrib(self.A_14), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratAType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratAType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.A_7 is not None and 'A_7' not in already_processed:
            already_processed.append('A_7')
            showIndent(outfile, level)
            outfile.write('A_7 = %s,\n' % (self.A_7,))
        if self.A_6 is not None and 'A_6' not in already_processed:
            already_processed.append('A_6')
            showIndent(outfile, level)
            outfile.write('A_6 = %s,\n' % (self.A_6,))
        if self.A_5 is not None and 'A_5' not in already_processed:
            already_processed.append('A_5')
            showIndent(outfile, level)
            outfile.write('A_5 = %s,\n' % (self.A_5,))
        if self.A_4 is not None and 'A_4' not in already_processed:
            already_processed.append('A_4')
            showIndent(outfile, level)
            outfile.write('A_4 = %s,\n' % (self.A_4,))
        if self.A_3 is not None and 'A_3' not in already_processed:
            already_processed.append('A_3')
            showIndent(outfile, level)
            outfile.write('A_3 = %s,\n' % (self.A_3,))
        if self.A_2 is not None and 'A_2' not in already_processed:
            already_processed.append('A_2')
            showIndent(outfile, level)
            outfile.write('A_2 = %s,\n' % (self.A_2,))
        if self.A_1 is not None and 'A_1' not in already_processed:
            already_processed.append('A_1')
            showIndent(outfile, level)
            outfile.write('A_1 = %s,\n' % (self.A_1,))
        if self.A_9 is not None and 'A_9' not in already_processed:
            already_processed.append('A_9')
            showIndent(outfile, level)
            outfile.write('A_9 = %s,\n' % (self.A_9,))
        if self.A_8 is not None and 'A_8' not in already_processed:
            already_processed.append('A_8')
            showIndent(outfile, level)
            outfile.write('A_8 = %s,\n' % (self.A_8,))
        if self.A_20 is not None and 'A_20' not in already_processed:
            already_processed.append('A_20')
            showIndent(outfile, level)
            outfile.write('A_20 = %s,\n' % (self.A_20,))
        if self.A_13 is not None and 'A_13' not in already_processed:
            already_processed.append('A_13')
            showIndent(outfile, level)
            outfile.write('A_13 = %s,\n' % (self.A_13,))
        if self.A_12 is not None and 'A_12' not in already_processed:
            already_processed.append('A_12')
            showIndent(outfile, level)
            outfile.write('A_12 = %s,\n' % (self.A_12,))
        if self.A_11 is not None and 'A_11' not in already_processed:
            already_processed.append('A_11')
            showIndent(outfile, level)
            outfile.write('A_11 = %s,\n' % (self.A_11,))
        if self.A_10 is not None and 'A_10' not in already_processed:
            already_processed.append('A_10')
            showIndent(outfile, level)
            outfile.write('A_10 = %s,\n' % (self.A_10,))
        if self.A_14 is not None and 'A_14' not in already_processed:
            already_processed.append('A_14')
            showIndent(outfile, level)
            outfile.write('A_14 = %s,\n' % (self.A_14,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('A_7')
        if value is not None and 'A_7' not in already_processed:
            already_processed.append('A_7')
            self.A_7 = value
        value = attrs.get('A_6')
        if value is not None and 'A_6' not in already_processed:
            already_processed.append('A_6')
            self.A_6 = value
        value = attrs.get('A_5')
        if value is not None and 'A_5' not in already_processed:
            already_processed.append('A_5')
            self.A_5 = value
        value = attrs.get('A_4')
        if value is not None and 'A_4' not in already_processed:
            already_processed.append('A_4')
            self.A_4 = value
        value = attrs.get('A_3')
        if value is not None and 'A_3' not in already_processed:
            already_processed.append('A_3')
            self.A_3 = value
        value = attrs.get('A_2')
        if value is not None and 'A_2' not in already_processed:
            already_processed.append('A_2')
            self.A_2 = value
        value = attrs.get('A_1')
        if value is not None and 'A_1' not in already_processed:
            already_processed.append('A_1')
            self.A_1 = value
        value = attrs.get('A_9')
        if value is not None and 'A_9' not in already_processed:
            already_processed.append('A_9')
            self.A_9 = value
        value = attrs.get('A_8')
        if value is not None and 'A_8' not in already_processed:
            already_processed.append('A_8')
            self.A_8 = value
        value = attrs.get('A_20')
        if value is not None and 'A_20' not in already_processed:
            already_processed.append('A_20')
            self.A_20 = value
        value = attrs.get('A_13')
        if value is not None and 'A_13' not in already_processed:
            already_processed.append('A_13')
            self.A_13 = value
        value = attrs.get('A_12')
        if value is not None and 'A_12' not in already_processed:
            already_processed.append('A_12')
            self.A_12 = value
        value = attrs.get('A_11')
        if value is not None and 'A_11' not in already_processed:
            already_processed.append('A_11')
            self.A_11 = value
        value = attrs.get('A_10')
        if value is not None and 'A_10' not in already_processed:
            already_processed.append('A_10')
            self.A_10 = value
        value = attrs.get('A_14')
        if value is not None and 'A_14' not in already_processed:
            already_processed.append('A_14')
            self.A_14 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratAType


class AsiguratB1Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B1_10=None, B1_15=None, B1_8=None, B1_9=None, B1_2=None, B1_3=None, B1_1=None, B1_6=None, B1_7=None, B1_4=None, B1_5=None, asiguratB11=None):
        self.B1_10 = _cast(None, B1_10)
        self.B1_15 = _cast(None, B1_15)
        self.B1_8 = _cast(None, B1_8)
        self.B1_9 = _cast(None, B1_9)
        self.B1_2 = _cast(None, B1_2)
        self.B1_3 = _cast(None, B1_3)
        self.B1_1 = _cast(None, B1_1)
        self.B1_6 = _cast(None, B1_6)
        self.B1_7 = _cast(None, B1_7)
        self.B1_4 = _cast(None, B1_4)
        self.B1_5 = _cast(None, B1_5)
        if asiguratB11 is None:
            self.asiguratB11 = []
        else:
            self.asiguratB11 = asiguratB11
    def factory(*args_, **kwargs_):
        if AsiguratB1Type.subclass:
            return AsiguratB1Type.subclass(*args_, **kwargs_)
        else:
            return AsiguratB1Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_asiguratB11(self): return self.asiguratB11
    def set_asiguratB11(self, asiguratB11): self.asiguratB11 = asiguratB11
    def add_asiguratB11(self, value): self.asiguratB11.append(value)
    def insert_asiguratB11(self, index, value): self.asiguratB11[index] = value
    def get_B1_10(self): return self.B1_10
    def set_B1_10(self, B1_10): self.B1_10 = B1_10
    def get_B1_15(self): return self.B1_15
    def set_B1_15(self, B1_15): self.B1_15 = B1_15
    def get_B1_8(self): return self.B1_8
    def set_B1_8(self, B1_8): self.B1_8 = B1_8
    def get_B1_9(self): return self.B1_9
    def set_B1_9(self, B1_9): self.B1_9 = B1_9
    def get_B1_2(self): return self.B1_2
    def set_B1_2(self, B1_2): self.B1_2 = B1_2
    def get_B1_3(self): return self.B1_3
    def set_B1_3(self, B1_3): self.B1_3 = B1_3
    def get_B1_1(self): return self.B1_1
    def set_B1_1(self, B1_1): self.B1_1 = B1_1
    def get_B1_6(self): return self.B1_6
    def set_B1_6(self, B1_6): self.B1_6 = B1_6
    def get_B1_7(self): return self.B1_7
    def set_B1_7(self, B1_7): self.B1_7 = B1_7
    def get_B1_4(self): return self.B1_4
    def set_B1_4(self, B1_4): self.B1_4 = B1_4
    def get_B1_5(self): return self.B1_5
    def set_B1_5(self, B1_5): self.B1_5 = B1_5
    def export(self, outfile, level, namespace_='', name_='AsiguratB1Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratB1Type')
        if self.hasContent_():
            outfile.write('>\n')
            self.exportChildren(outfile, level + 1, namespace_, name_)
            showIndent(outfile, level)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratB1Type'):
        if self.B1_10 is not None and 'B1_10' not in already_processed:
            already_processed.append('B1_10')
            outfile.write(' B1_10=%s' % (quote_attrib(self.B1_10), ))
        if self.B1_15 is not None and 'B1_15' not in already_processed:
            already_processed.append('B1_15')
            outfile.write(' B1_15=%s' % (quote_attrib(self.B1_15), ))
        if self.B1_8 is not None and 'B1_8' not in already_processed:
            already_processed.append('B1_8')
            outfile.write(' B1_8=%s' % (quote_attrib(self.B1_8), ))
        if self.B1_9 is not None and 'B1_9' not in already_processed:
            already_processed.append('B1_9')
            outfile.write(' B1_9=%s' % (quote_attrib(self.B1_9), ))
        outfile.write(' B1_2=%s' % (quote_attrib(self.B1_2), ))
        outfile.write(' B1_3=%s' % (quote_attrib(self.B1_3), ))
        outfile.write(' B1_1=%s' % (quote_attrib(self.B1_1), ))
        if self.B1_6 is not None and 'B1_6' not in already_processed:
            already_processed.append('B1_6')
            outfile.write(' B1_6=%s' % (quote_attrib(self.B1_6), ))
        if self.B1_7 is not None and 'B1_7' not in already_processed:
            already_processed.append('B1_7')
            outfile.write(' B1_7=%s' % (quote_attrib(self.B1_7), ))
        outfile.write(' B1_4=%s' % (quote_attrib(self.B1_4), ))
        if self.B1_5 is not None and 'B1_5' not in already_processed:
            already_processed.append('B1_5')
            outfile.write(' B1_5=%s' % (quote_attrib(self.B1_5), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratB1Type'):
        for asiguratB11_ in self.asiguratB11:
            asiguratB11_.export(outfile, level, namespace_, name_='asiguratB11')
    def hasContent_(self):
        if (
            self.asiguratB11
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratB1Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B1_10 is not None and 'B1_10' not in already_processed:
            already_processed.append('B1_10')
            showIndent(outfile, level)
            outfile.write('B1_10 = %s,\n' % (self.B1_10,))
        if self.B1_15 is not None and 'B1_15' not in already_processed:
            already_processed.append('B1_15')
            showIndent(outfile, level)
            outfile.write('B1_15 = %s,\n' % (self.B1_15,))
        if self.B1_8 is not None and 'B1_8' not in already_processed:
            already_processed.append('B1_8')
            showIndent(outfile, level)
            outfile.write('B1_8 = %s,\n' % (self.B1_8,))
        if self.B1_9 is not None and 'B1_9' not in already_processed:
            already_processed.append('B1_9')
            showIndent(outfile, level)
            outfile.write('B1_9 = %s,\n' % (self.B1_9,))
        if self.B1_2 is not None and 'B1_2' not in already_processed:
            already_processed.append('B1_2')
            showIndent(outfile, level)
            outfile.write('B1_2 = %s,\n' % (self.B1_2,))
        if self.B1_3 is not None and 'B1_3' not in already_processed:
            already_processed.append('B1_3')
            showIndent(outfile, level)
            outfile.write('B1_3 = %s,\n' % (self.B1_3,))
        if self.B1_1 is not None and 'B1_1' not in already_processed:
            already_processed.append('B1_1')
            showIndent(outfile, level)
            outfile.write('B1_1 = %s,\n' % (self.B1_1,))
        if self.B1_6 is not None and 'B1_6' not in already_processed:
            already_processed.append('B1_6')
            showIndent(outfile, level)
            outfile.write('B1_6 = %s,\n' % (self.B1_6,))
        if self.B1_7 is not None and 'B1_7' not in already_processed:
            already_processed.append('B1_7')
            showIndent(outfile, level)
            outfile.write('B1_7 = %s,\n' % (self.B1_7,))
        if self.B1_4 is not None and 'B1_4' not in already_processed:
            already_processed.append('B1_4')
            showIndent(outfile, level)
            outfile.write('B1_4 = %s,\n' % (self.B1_4,))
        if self.B1_5 is not None and 'B1_5' not in already_processed:
            already_processed.append('B1_5')
            showIndent(outfile, level)
            outfile.write('B1_5 = %s,\n' % (self.B1_5,))
    def exportLiteralChildren(self, outfile, level, name_):
        showIndent(outfile, level)
        outfile.write('asiguratB11=[\n')
        level += 1
        for asiguratB11_ in self.asiguratB11:
            showIndent(outfile, level)
            outfile.write('model_.AsiguratB11Type(\n')
            asiguratB11_.exportLiteral(outfile, level, name_='AsiguratB11Type')
            showIndent(outfile, level)
            outfile.write('),\n')
        level -= 1
        showIndent(outfile, level)
        outfile.write('],\n')
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B1_10')
        if value is not None and 'B1_10' not in already_processed:
            already_processed.append('B1_10')
            self.B1_10 = value
        value = attrs.get('B1_15')
        if value is not None and 'B1_15' not in already_processed:
            already_processed.append('B1_15')
            self.B1_15 = value
        value = attrs.get('B1_8')
        if value is not None and 'B1_8' not in already_processed:
            already_processed.append('B1_8')
            self.B1_8 = value
        value = attrs.get('B1_9')
        if value is not None and 'B1_9' not in already_processed:
            already_processed.append('B1_9')
            self.B1_9 = value
        value = attrs.get('B1_2')
        if value is not None and 'B1_2' not in already_processed:
            already_processed.append('B1_2')
            self.B1_2 = value
        value = attrs.get('B1_3')
        if value is not None and 'B1_3' not in already_processed:
            already_processed.append('B1_3')
            self.B1_3 = value
        value = attrs.get('B1_1')
        if value is not None and 'B1_1' not in already_processed:
            already_processed.append('B1_1')
            self.B1_1 = value
        value = attrs.get('B1_6')
        if value is not None and 'B1_6' not in already_processed:
            already_processed.append('B1_6')
            self.B1_6 = value
        value = attrs.get('B1_7')
        if value is not None and 'B1_7' not in already_processed:
            already_processed.append('B1_7')
            self.B1_7 = value
        value = attrs.get('B1_4')
        if value is not None and 'B1_4' not in already_processed:
            already_processed.append('B1_4')
            self.B1_4 = value
        value = attrs.get('B1_5')
        if value is not None and 'B1_5' not in already_processed:
            already_processed.append('B1_5')
            self.B1_5 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        if nodeName_ == 'asiguratB11': 
            obj_ = AsiguratB11Type.factory()
            obj_.build(child_)
            self.asiguratB11.append(obj_)
# end class AsiguratB1Type


class AsiguratB11Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B11_41=None, B11_43=None, B11_42=None, B11_71=None, B11_72=None, B11_73=None, B11_5=None, B11_6=None, B11_1=None, B11_2=None, B11_3=None, valueOf_=None):
        self.B11_41 = _cast(None, B11_41)
        self.B11_43 = _cast(None, B11_43)
        self.B11_42 = _cast(None, B11_42)
        self.B11_71 = _cast(None, B11_71)
        self.B11_72 = _cast(None, B11_72)
        self.B11_73 = _cast(None, B11_73)
        self.B11_5 = _cast(None, B11_5)
        self.B11_6 = _cast(None, B11_6)
        self.B11_1 = _cast(None, B11_1)
        self.B11_2 = _cast(None, B11_2)
        self.B11_3 = _cast(None, B11_3)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratB11Type.subclass:
            return AsiguratB11Type.subclass(*args_, **kwargs_)
        else:
            return AsiguratB11Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_B11_41(self): return self.B11_41
    def set_B11_41(self, B11_41): self.B11_41 = B11_41
    def get_B11_43(self): return self.B11_43
    def set_B11_43(self, B11_43): self.B11_43 = B11_43
    def get_B11_42(self): return self.B11_42
    def set_B11_42(self, B11_42): self.B11_42 = B11_42
    def get_B11_71(self): return self.B11_71
    def set_B11_71(self, B11_71): self.B11_71 = B11_71
    def get_B11_72(self): return self.B11_72
    def set_B11_72(self, B11_72): self.B11_72 = B11_72
    def get_B11_73(self): return self.B11_73
    def set_B11_73(self, B11_73): self.B11_73 = B11_73
    def get_B11_5(self): return self.B11_5
    def set_B11_5(self, B11_5): self.B11_5 = B11_5
    def get_B11_6(self): return self.B11_6
    def set_B11_6(self, B11_6): self.B11_6 = B11_6
    def get_B11_1(self): return self.B11_1
    def set_B11_1(self, B11_1): self.B11_1 = B11_1
    def get_B11_2(self): return self.B11_2
    def set_B11_2(self, B11_2): self.B11_2 = B11_2
    def get_B11_3(self): return self.B11_3
    def set_B11_3(self, B11_3): self.B11_3 = B11_3
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratB11Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratB11Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratB11Type'):
        if self.B11_41 is not None and 'B11_41' not in already_processed:
            already_processed.append('B11_41')
            outfile.write(' B11_41=%s' % (quote_attrib(self.B11_41), ))
        if self.B11_43 is not None and 'B11_43' not in already_processed:
            already_processed.append('B11_43')
            outfile.write(' B11_43=%s' % (quote_attrib(self.B11_43), ))
        if self.B11_42 is not None and 'B11_42' not in already_processed:
            already_processed.append('B11_42')
            outfile.write(' B11_42=%s' % (quote_attrib(self.B11_42), ))
        if self.B11_71 is not None and 'B11_71' not in already_processed:
            already_processed.append('B11_71')
            outfile.write(' B11_71=%s' % (quote_attrib(self.B11_71), ))
        if self.B11_72 is not None and 'B11_72' not in already_processed:
            already_processed.append('B11_72')
            outfile.write(' B11_72=%s' % (quote_attrib(self.B11_72), ))
        if self.B11_73 is not None and 'B11_73' not in already_processed:
            already_processed.append('B11_73')
            outfile.write(' B11_73=%s' % (quote_attrib(self.B11_73), ))
        if self.B11_5 is not None and 'B11_5' not in already_processed:
            already_processed.append('B11_5')
            outfile.write(' B11_5=%s' % (quote_attrib(self.B11_5), ))
        if self.B11_6 is not None and 'B11_6' not in already_processed:
            already_processed.append('B11_6')
            outfile.write(' B11_6=%s' % (quote_attrib(self.B11_6), ))
        outfile.write(' B11_1=%s' % (quote_attrib(self.B11_1), ))
        if self.B11_2 is not None and 'B11_2' not in already_processed:
            already_processed.append('B11_2')
            outfile.write(' B11_2=%s' % (quote_attrib(self.B11_2), ))
        if self.B11_3 is not None and 'B11_3' not in already_processed:
            already_processed.append('B11_3')
            outfile.write(' B11_3=%s' % (quote_attrib(self.B11_3), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratB11Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratB11Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B11_41 is not None and 'B11_41' not in already_processed:
            already_processed.append('B11_41')
            showIndent(outfile, level)
            outfile.write('B11_41 = %s,\n' % (self.B11_41,))
        if self.B11_43 is not None and 'B11_43' not in already_processed:
            already_processed.append('B11_43')
            showIndent(outfile, level)
            outfile.write('B11_43 = %s,\n' % (self.B11_43,))
        if self.B11_42 is not None and 'B11_42' not in already_processed:
            already_processed.append('B11_42')
            showIndent(outfile, level)
            outfile.write('B11_42 = %s,\n' % (self.B11_42,))
        if self.B11_71 is not None and 'B11_71' not in already_processed:
            already_processed.append('B11_71')
            showIndent(outfile, level)
            outfile.write('B11_71 = %s,\n' % (self.B11_71,))
        if self.B11_72 is not None and 'B11_72' not in already_processed:
            already_processed.append('B11_72')
            showIndent(outfile, level)
            outfile.write('B11_72 = %s,\n' % (self.B11_72,))
        if self.B11_73 is not None and 'B11_73' not in already_processed:
            already_processed.append('B11_73')
            showIndent(outfile, level)
            outfile.write('B11_73 = %s,\n' % (self.B11_73,))
        if self.B11_5 is not None and 'B11_5' not in already_processed:
            already_processed.append('B11_5')
            showIndent(outfile, level)
            outfile.write('B11_5 = %s,\n' % (self.B11_5,))
        if self.B11_6 is not None and 'B11_6' not in already_processed:
            already_processed.append('B11_6')
            showIndent(outfile, level)
            outfile.write('B11_6 = %s,\n' % (self.B11_6,))
        if self.B11_1 is not None and 'B11_1' not in already_processed:
            already_processed.append('B11_1')
            showIndent(outfile, level)
            outfile.write('B11_1 = %s,\n' % (self.B11_1,))
        if self.B11_2 is not None and 'B11_2' not in already_processed:
            already_processed.append('B11_2')
            showIndent(outfile, level)
            outfile.write('B11_2 = %s,\n' % (self.B11_2,))
        if self.B11_3 is not None and 'B11_3' not in already_processed:
            already_processed.append('B11_3')
            showIndent(outfile, level)
            outfile.write('B11_3 = %s,\n' % (self.B11_3,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B11_41')
        if value is not None and 'B11_41' not in already_processed:
            already_processed.append('B11_41')
            self.B11_41 = value
        value = attrs.get('B11_43')
        if value is not None and 'B11_43' not in already_processed:
            already_processed.append('B11_43')
            self.B11_43 = value
        value = attrs.get('B11_42')
        if value is not None and 'B11_42' not in already_processed:
            already_processed.append('B11_42')
            self.B11_42 = value
        value = attrs.get('B11_71')
        if value is not None and 'B11_71' not in already_processed:
            already_processed.append('B11_71')
            self.B11_71 = value
        value = attrs.get('B11_72')
        if value is not None and 'B11_72' not in already_processed:
            already_processed.append('B11_72')
            self.B11_72 = value
        value = attrs.get('B11_73')
        if value is not None and 'B11_73' not in already_processed:
            already_processed.append('B11_73')
            self.B11_73 = value
        value = attrs.get('B11_5')
        if value is not None and 'B11_5' not in already_processed:
            already_processed.append('B11_5')
            self.B11_5 = value
        value = attrs.get('B11_6')
        if value is not None and 'B11_6' not in already_processed:
            already_processed.append('B11_6')
            self.B11_6 = value
        value = attrs.get('B11_1')
        if value is not None and 'B11_1' not in already_processed:
            already_processed.append('B11_1')
            self.B11_1 = value
        value = attrs.get('B11_2')
        if value is not None and 'B11_2' not in already_processed:
            already_processed.append('B11_2')
            self.B11_2 = value
        value = attrs.get('B11_3')
        if value is not None and 'B11_3' not in already_processed:
            already_processed.append('B11_3')
            self.B11_3 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratB11Type


class AsiguratB2Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B2_5=None, B2_4=None, B2_7=None, B2_6=None, B2_1=None, B2_3=None, B2_2=None, valueOf_=None):
        self.B2_5 = _cast(None, B2_5)
        self.B2_4 = _cast(None, B2_4)
        self.B2_7 = _cast(None, B2_7)
        self.B2_6 = _cast(None, B2_6)
        self.B2_1 = _cast(None, B2_1)
        self.B2_3 = _cast(None, B2_3)
        self.B2_2 = _cast(None, B2_2)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratB2Type.subclass:
            return AsiguratB2Type.subclass(*args_, **kwargs_)
        else:
            return AsiguratB2Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_B2_5(self): return self.B2_5
    def set_B2_5(self, B2_5): self.B2_5 = B2_5
    def get_B2_4(self): return self.B2_4
    def set_B2_4(self, B2_4): self.B2_4 = B2_4
    def get_B2_7(self): return self.B2_7
    def set_B2_7(self, B2_7): self.B2_7 = B2_7
    def get_B2_6(self): return self.B2_6
    def set_B2_6(self, B2_6): self.B2_6 = B2_6
    def get_B2_1(self): return self.B2_1
    def set_B2_1(self, B2_1): self.B2_1 = B2_1
    def get_B2_3(self): return self.B2_3
    def set_B2_3(self, B2_3): self.B2_3 = B2_3
    def get_B2_2(self): return self.B2_2
    def set_B2_2(self, B2_2): self.B2_2 = B2_2
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratB2Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratB2Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratB2Type'):
        if self.B2_5 is not None and 'B2_5' not in already_processed:
            already_processed.append('B2_5')
            outfile.write(' B2_5=%s' % (quote_attrib(self.B2_5), ))
        if self.B2_4 is not None and 'B2_4' not in already_processed:
            already_processed.append('B2_4')
            outfile.write(' B2_4=%s' % (quote_attrib(self.B2_4), ))
        if self.B2_7 is not None and 'B2_7' not in already_processed:
            already_processed.append('B2_7')
            outfile.write(' B2_7=%s' % (quote_attrib(self.B2_7), ))
        if self.B2_6 is not None and 'B2_6' not in already_processed:
            already_processed.append('B2_6')
            outfile.write(' B2_6=%s' % (quote_attrib(self.B2_6), ))
        if self.B2_1 is not None and 'B2_1' not in already_processed:
            already_processed.append('B2_1')
            outfile.write(' B2_1=%s' % (quote_attrib(self.B2_1), ))
        if self.B2_3 is not None and 'B2_3' not in already_processed:
            already_processed.append('B2_3')
            outfile.write(' B2_3=%s' % (quote_attrib(self.B2_3), ))
        if self.B2_2 is not None and 'B2_2' not in already_processed:
            already_processed.append('B2_2')
            outfile.write(' B2_2=%s' % (quote_attrib(self.B2_2), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratB2Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratB2Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B2_5 is not None and 'B2_5' not in already_processed:
            already_processed.append('B2_5')
            showIndent(outfile, level)
            outfile.write('B2_5 = %s,\n' % (self.B2_5,))
        if self.B2_4 is not None and 'B2_4' not in already_processed:
            already_processed.append('B2_4')
            showIndent(outfile, level)
            outfile.write('B2_4 = %s,\n' % (self.B2_4,))
        if self.B2_7 is not None and 'B2_7' not in already_processed:
            already_processed.append('B2_7')
            showIndent(outfile, level)
            outfile.write('B2_7 = %s,\n' % (self.B2_7,))
        if self.B2_6 is not None and 'B2_6' not in already_processed:
            already_processed.append('B2_6')
            showIndent(outfile, level)
            outfile.write('B2_6 = %s,\n' % (self.B2_6,))
        if self.B2_1 is not None and 'B2_1' not in already_processed:
            already_processed.append('B2_1')
            showIndent(outfile, level)
            outfile.write('B2_1 = %s,\n' % (self.B2_1,))
        if self.B2_3 is not None and 'B2_3' not in already_processed:
            already_processed.append('B2_3')
            showIndent(outfile, level)
            outfile.write('B2_3 = %s,\n' % (self.B2_3,))
        if self.B2_2 is not None and 'B2_2' not in already_processed:
            already_processed.append('B2_2')
            showIndent(outfile, level)
            outfile.write('B2_2 = %s,\n' % (self.B2_2,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B2_5')
        if value is not None and 'B2_5' not in already_processed:
            already_processed.append('B2_5')
            self.B2_5 = value
        value = attrs.get('B2_4')
        if value is not None and 'B2_4' not in already_processed:
            already_processed.append('B2_4')
            self.B2_4 = value
        value = attrs.get('B2_7')
        if value is not None and 'B2_7' not in already_processed:
            already_processed.append('B2_7')
            self.B2_7 = value
        value = attrs.get('B2_6')
        if value is not None and 'B2_6' not in already_processed:
            already_processed.append('B2_6')
            self.B2_6 = value
        value = attrs.get('B2_1')
        if value is not None and 'B2_1' not in already_processed:
            already_processed.append('B2_1')
            self.B2_1 = value
        value = attrs.get('B2_3')
        if value is not None and 'B2_3' not in already_processed:
            already_processed.append('B2_3')
            self.B2_3 = value
        value = attrs.get('B2_2')
        if value is not None and 'B2_2' not in already_processed:
            already_processed.append('B2_2')
            self.B2_2 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratB2Type


class AsiguratB3Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B3_12=None, B3_13=None, B3_10=None, B3_11=None, B3_4=None, B3_5=None, B3_6=None, B3_7=None, B3_1=None, B3_2=None, B3_3=None, B3_8=None, B3_9=None, valueOf_=None):
        self.B3_12 = _cast(None, B3_12)
        self.B3_13 = _cast(None, B3_13)
        self.B3_10 = _cast(None, B3_10)
        self.B3_11 = _cast(None, B3_11)
        self.B3_4 = _cast(None, B3_4)
        self.B3_5 = _cast(None, B3_5)
        self.B3_6 = _cast(None, B3_6)
        self.B3_7 = _cast(None, B3_7)
        self.B3_1 = _cast(None, B3_1)
        self.B3_2 = _cast(None, B3_2)
        self.B3_3 = _cast(None, B3_3)
        self.B3_8 = _cast(None, B3_8)
        self.B3_9 = _cast(None, B3_9)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratB3Type.subclass:
            return AsiguratB3Type.subclass(*args_, **kwargs_)
        else:
            return AsiguratB3Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_B3_12(self): return self.B3_12
    def set_B3_12(self, B3_12): self.B3_12 = B3_12
    def get_B3_13(self): return self.B3_13
    def set_B3_13(self, B3_13): self.B3_13 = B3_13
    def get_B3_10(self): return self.B3_10
    def set_B3_10(self, B3_10): self.B3_10 = B3_10
    def get_B3_11(self): return self.B3_11
    def set_B3_11(self, B3_11): self.B3_11 = B3_11
    def get_B3_4(self): return self.B3_4
    def set_B3_4(self, B3_4): self.B3_4 = B3_4
    def get_B3_5(self): return self.B3_5
    def set_B3_5(self, B3_5): self.B3_5 = B3_5
    def get_B3_6(self): return self.B3_6
    def set_B3_6(self, B3_6): self.B3_6 = B3_6
    def get_B3_7(self): return self.B3_7
    def set_B3_7(self, B3_7): self.B3_7 = B3_7
    def get_B3_1(self): return self.B3_1
    def set_B3_1(self, B3_1): self.B3_1 = B3_1
    def get_B3_2(self): return self.B3_2
    def set_B3_2(self, B3_2): self.B3_2 = B3_2
    def get_B3_3(self): return self.B3_3
    def set_B3_3(self, B3_3): self.B3_3 = B3_3
    def get_B3_8(self): return self.B3_8
    def set_B3_8(self, B3_8): self.B3_8 = B3_8
    def get_B3_9(self): return self.B3_9
    def set_B3_9(self, B3_9): self.B3_9 = B3_9
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratB3Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratB3Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratB3Type'):
        if self.B3_12 is not None and 'B3_12' not in already_processed:
            already_processed.append('B3_12')
            outfile.write(' B3_12=%s' % (quote_attrib(self.B3_12), ))
        if self.B3_13 is not None and 'B3_13' not in already_processed:
            already_processed.append('B3_13')
            outfile.write(' B3_13=%s' % (quote_attrib(self.B3_13), ))
        if self.B3_10 is not None and 'B3_10' not in already_processed:
            already_processed.append('B3_10')
            outfile.write(' B3_10=%s' % (quote_attrib(self.B3_10), ))
        if self.B3_11 is not None and 'B3_11' not in already_processed:
            already_processed.append('B3_11')
            outfile.write(' B3_11=%s' % (quote_attrib(self.B3_11), ))
        if self.B3_4 is not None and 'B3_4' not in already_processed:
            already_processed.append('B3_4')
            outfile.write(' B3_4=%s' % (quote_attrib(self.B3_4), ))
        if self.B3_5 is not None and 'B3_5' not in already_processed:
            already_processed.append('B3_5')
            outfile.write(' B3_5=%s' % (quote_attrib(self.B3_5), ))
        if self.B3_6 is not None and 'B3_6' not in already_processed:
            already_processed.append('B3_6')
            outfile.write(' B3_6=%s' % (quote_attrib(self.B3_6), ))
        if self.B3_7 is not None and 'B3_7' not in already_processed:
            already_processed.append('B3_7')
            outfile.write(' B3_7=%s' % (quote_attrib(self.B3_7), ))
        if self.B3_1 is not None and 'B3_1' not in already_processed:
            already_processed.append('B3_1')
            outfile.write(' B3_1=%s' % (quote_attrib(self.B3_1), ))
        if self.B3_2 is not None and 'B3_2' not in already_processed:
            already_processed.append('B3_2')
            outfile.write(' B3_2=%s' % (quote_attrib(self.B3_2), ))
        if self.B3_3 is not None and 'B3_3' not in already_processed:
            already_processed.append('B3_3')
            outfile.write(' B3_3=%s' % (quote_attrib(self.B3_3), ))
        if self.B3_8 is not None and 'B3_8' not in already_processed:
            already_processed.append('B3_8')
            outfile.write(' B3_8=%s' % (quote_attrib(self.B3_8), ))
        if self.B3_9 is not None and 'B3_9' not in already_processed:
            already_processed.append('B3_9')
            outfile.write(' B3_9=%s' % (quote_attrib(self.B3_9), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratB3Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratB3Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B3_12 is not None and 'B3_12' not in already_processed:
            already_processed.append('B3_12')
            showIndent(outfile, level)
            outfile.write('B3_12 = %s,\n' % (self.B3_12,))
        if self.B3_13 is not None and 'B3_13' not in already_processed:
            already_processed.append('B3_13')
            showIndent(outfile, level)
            outfile.write('B3_13 = %s,\n' % (self.B3_13,))
        if self.B3_10 is not None and 'B3_10' not in already_processed:
            already_processed.append('B3_10')
            showIndent(outfile, level)
            outfile.write('B3_10 = %s,\n' % (self.B3_10,))
        if self.B3_11 is not None and 'B3_11' not in already_processed:
            already_processed.append('B3_11')
            showIndent(outfile, level)
            outfile.write('B3_11 = %s,\n' % (self.B3_11,))
        if self.B3_4 is not None and 'B3_4' not in already_processed:
            already_processed.append('B3_4')
            showIndent(outfile, level)
            outfile.write('B3_4 = %s,\n' % (self.B3_4,))
        if self.B3_5 is not None and 'B3_5' not in already_processed:
            already_processed.append('B3_5')
            showIndent(outfile, level)
            outfile.write('B3_5 = %s,\n' % (self.B3_5,))
        if self.B3_6 is not None and 'B3_6' not in already_processed:
            already_processed.append('B3_6')
            showIndent(outfile, level)
            outfile.write('B3_6 = %s,\n' % (self.B3_6,))
        if self.B3_7 is not None and 'B3_7' not in already_processed:
            already_processed.append('B3_7')
            showIndent(outfile, level)
            outfile.write('B3_7 = %s,\n' % (self.B3_7,))
        if self.B3_1 is not None and 'B3_1' not in already_processed:
            already_processed.append('B3_1')
            showIndent(outfile, level)
            outfile.write('B3_1 = %s,\n' % (self.B3_1,))
        if self.B3_2 is not None and 'B3_2' not in already_processed:
            already_processed.append('B3_2')
            showIndent(outfile, level)
            outfile.write('B3_2 = %s,\n' % (self.B3_2,))
        if self.B3_3 is not None and 'B3_3' not in already_processed:
            already_processed.append('B3_3')
            showIndent(outfile, level)
            outfile.write('B3_3 = %s,\n' % (self.B3_3,))
        if self.B3_8 is not None and 'B3_8' not in already_processed:
            already_processed.append('B3_8')
            showIndent(outfile, level)
            outfile.write('B3_8 = %s,\n' % (self.B3_8,))
        if self.B3_9 is not None and 'B3_9' not in already_processed:
            already_processed.append('B3_9')
            showIndent(outfile, level)
            outfile.write('B3_9 = %s,\n' % (self.B3_9,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B3_12')
        if value is not None and 'B3_12' not in already_processed:
            already_processed.append('B3_12')
            self.B3_12 = value
        value = attrs.get('B3_13')
        if value is not None and 'B3_13' not in already_processed:
            already_processed.append('B3_13')
            self.B3_13 = value
        value = attrs.get('B3_10')
        if value is not None and 'B3_10' not in already_processed:
            already_processed.append('B3_10')
            self.B3_10 = value
        value = attrs.get('B3_11')
        if value is not None and 'B3_11' not in already_processed:
            already_processed.append('B3_11')
            self.B3_11 = value
        value = attrs.get('B3_4')
        if value is not None and 'B3_4' not in already_processed:
            already_processed.append('B3_4')
            self.B3_4 = value
        value = attrs.get('B3_5')
        if value is not None and 'B3_5' not in already_processed:
            already_processed.append('B3_5')
            self.B3_5 = value
        value = attrs.get('B3_6')
        if value is not None and 'B3_6' not in already_processed:
            already_processed.append('B3_6')
            self.B3_6 = value
        value = attrs.get('B3_7')
        if value is not None and 'B3_7' not in already_processed:
            already_processed.append('B3_7')
            self.B3_7 = value
        value = attrs.get('B3_1')
        if value is not None and 'B3_1' not in already_processed:
            already_processed.append('B3_1')
            self.B3_1 = value
        value = attrs.get('B3_2')
        if value is not None and 'B3_2' not in already_processed:
            already_processed.append('B3_2')
            self.B3_2 = value
        value = attrs.get('B3_3')
        if value is not None and 'B3_3' not in already_processed:
            already_processed.append('B3_3')
            self.B3_3 = value
        value = attrs.get('B3_8')
        if value is not None and 'B3_8' not in already_processed:
            already_processed.append('B3_8')
            self.B3_8 = value
        value = attrs.get('B3_9')
        if value is not None and 'B3_9' not in already_processed:
            already_processed.append('B3_9')
            self.B3_9 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratB3Type


class AsiguratB4Type(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, B4_8=None, B4_7=None, B4_6=None, B4_5=None, B4_4=None, B4_3=None, B4_2=None, B4_1=None, B4_14=None, valueOf_=None):
        self.B4_8 = _cast(None, B4_8)
        self.B4_7 = _cast(None, B4_7)
        self.B4_6 = _cast(None, B4_6)
        self.B4_5 = _cast(None, B4_5)
        self.B4_4 = _cast(None, B4_4)
        self.B4_3 = _cast(None, B4_3)
        self.B4_2 = _cast(None, B4_2)
        self.B4_1 = _cast(None, B4_1)
        self.B4_14 = _cast(None, B4_14)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratB4Type.subclass:
            return AsiguratB4Type.subclass(*args_, **kwargs_)
        else:
            return AsiguratB4Type(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_B4_8(self): return self.B4_8
    def set_B4_8(self, B4_8): self.B4_8 = B4_8
    def get_B4_7(self): return self.B4_7
    def set_B4_7(self, B4_7): self.B4_7 = B4_7
    def get_B4_6(self): return self.B4_6
    def set_B4_6(self, B4_6): self.B4_6 = B4_6
    def get_B4_5(self): return self.B4_5
    def set_B4_5(self, B4_5): self.B4_5 = B4_5
    def get_B4_4(self): return self.B4_4
    def set_B4_4(self, B4_4): self.B4_4 = B4_4
    def get_B4_3(self): return self.B4_3
    def set_B4_3(self, B4_3): self.B4_3 = B4_3
    def get_B4_2(self): return self.B4_2
    def set_B4_2(self, B4_2): self.B4_2 = B4_2
    def get_B4_1(self): return self.B4_1
    def set_B4_1(self, B4_1): self.B4_1 = B4_1
    def get_B4_14(self): return self.B4_14
    def set_B4_14(self, B4_14): self.B4_14 = B4_14
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratB4Type', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratB4Type')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratB4Type'):
        if self.B4_8 is not None and 'B4_8' not in already_processed:
            already_processed.append('B4_8')
            outfile.write(' B4_8=%s' % (quote_attrib(self.B4_8), ))
        if self.B4_7 is not None and 'B4_7' not in already_processed:
            already_processed.append('B4_7')
            outfile.write(' B4_7=%s' % (quote_attrib(self.B4_7), ))
        if self.B4_6 is not None and 'B4_6' not in already_processed:
            already_processed.append('B4_6')
            outfile.write(' B4_6=%s' % (quote_attrib(self.B4_6), ))
        if self.B4_5 is not None and 'B4_5' not in already_processed:
            already_processed.append('B4_5')
            outfile.write(' B4_5=%s' % (quote_attrib(self.B4_5), ))
        if self.B4_4 is not None and 'B4_4' not in already_processed:
            already_processed.append('B4_4')
            outfile.write(' B4_4=%s' % (quote_attrib(self.B4_4), ))
        if self.B4_3 is not None and 'B4_3' not in already_processed:
            already_processed.append('B4_3')
            outfile.write(' B4_3=%s' % (quote_attrib(self.B4_3), ))
        if self.B4_2 is not None and 'B4_2' not in already_processed:
            already_processed.append('B4_2')
            outfile.write(' B4_2=%s' % (quote_attrib(self.B4_2), ))
        if self.B4_1 is not None and 'B4_1' not in already_processed:
            already_processed.append('B4_1')
            outfile.write(' B4_1=%s' % (quote_attrib(self.B4_1), ))
        if self.B4_14 is not None and 'B4_14' not in already_processed:
            already_processed.append('B4_14')
            outfile.write(' B4_14=%s' % (quote_attrib(self.B4_14), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratB4Type'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratB4Type'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.B4_8 is not None and 'B4_8' not in already_processed:
            already_processed.append('B4_8')
            showIndent(outfile, level)
            outfile.write('B4_8 = %s,\n' % (self.B4_8,))
        if self.B4_7 is not None and 'B4_7' not in already_processed:
            already_processed.append('B4_7')
            showIndent(outfile, level)
            outfile.write('B4_7 = %s,\n' % (self.B4_7,))
        if self.B4_6 is not None and 'B4_6' not in already_processed:
            already_processed.append('B4_6')
            showIndent(outfile, level)
            outfile.write('B4_6 = %s,\n' % (self.B4_6,))
        if self.B4_5 is not None and 'B4_5' not in already_processed:
            already_processed.append('B4_5')
            showIndent(outfile, level)
            outfile.write('B4_5 = %s,\n' % (self.B4_5,))
        if self.B4_4 is not None and 'B4_4' not in already_processed:
            already_processed.append('B4_4')
            showIndent(outfile, level)
            outfile.write('B4_4 = %s,\n' % (self.B4_4,))
        if self.B4_3 is not None and 'B4_3' not in already_processed:
            already_processed.append('B4_3')
            showIndent(outfile, level)
            outfile.write('B4_3 = %s,\n' % (self.B4_3,))
        if self.B4_2 is not None and 'B4_2' not in already_processed:
            already_processed.append('B4_2')
            showIndent(outfile, level)
            outfile.write('B4_2 = %s,\n' % (self.B4_2,))
        if self.B4_1 is not None and 'B4_1' not in already_processed:
            already_processed.append('B4_1')
            showIndent(outfile, level)
            outfile.write('B4_1 = %s,\n' % (self.B4_1,))
        if self.B4_14 is not None and 'B4_14' not in already_processed:
            already_processed.append('B4_14')
            showIndent(outfile, level)
            outfile.write('B4_14 = %s,\n' % (self.B4_14,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('B4_8')
        if value is not None and 'B4_8' not in already_processed:
            already_processed.append('B4_8')
            self.B4_8 = value
        value = attrs.get('B4_7')
        if value is not None and 'B4_7' not in already_processed:
            already_processed.append('B4_7')
            self.B4_7 = value
        value = attrs.get('B4_6')
        if value is not None and 'B4_6' not in already_processed:
            already_processed.append('B4_6')
            self.B4_6 = value
        value = attrs.get('B4_5')
        if value is not None and 'B4_5' not in already_processed:
            already_processed.append('B4_5')
            self.B4_5 = value
        value = attrs.get('B4_4')
        if value is not None and 'B4_4' not in already_processed:
            already_processed.append('B4_4')
            self.B4_4 = value
        value = attrs.get('B4_3')
        if value is not None and 'B4_3' not in already_processed:
            already_processed.append('B4_3')
            self.B4_3 = value
        value = attrs.get('B4_2')
        if value is not None and 'B4_2' not in already_processed:
            already_processed.append('B4_2')
            self.B4_2 = value
        value = attrs.get('B4_1')
        if value is not None and 'B4_1' not in already_processed:
            already_processed.append('B4_1')
            self.B4_1 = value
        value = attrs.get('B4_14')
        if value is not None and 'B4_14' not in already_processed:
            already_processed.append('B4_14')
            self.B4_14 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratB4Type


class AsiguratCType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, C_19=None, C_18=None, C_17=None, C_11=None, C_10=None, C_1=None, C_3=None, C_2=None, C_5=None, C_4=None, C_7=None, C_6=None, C_9=None, C_8=None, valueOf_=None):
        self.C_19 = _cast(None, C_19)
        self.C_18 = _cast(None, C_18)
        self.C_17 = _cast(None, C_17)
        self.C_11 = _cast(None, C_11)
        self.C_10 = _cast(None, C_10)
        self.C_1 = _cast(None, C_1)
        self.C_3 = _cast(None, C_3)
        self.C_2 = _cast(None, C_2)
        self.C_5 = _cast(None, C_5)
        self.C_4 = _cast(None, C_4)
        self.C_7 = _cast(None, C_7)
        self.C_6 = _cast(None, C_6)
        self.C_9 = _cast(None, C_9)
        self.C_8 = _cast(None, C_8)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratCType.subclass:
            return AsiguratCType.subclass(*args_, **kwargs_)
        else:
            return AsiguratCType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_C_19(self): return self.C_19
    def set_C_19(self, C_19): self.C_19 = C_19
    def get_C_18(self): return self.C_18
    def set_C_18(self, C_18): self.C_18 = C_18
    def get_C_17(self): return self.C_17
    def set_C_17(self, C_17): self.C_17 = C_17
    def get_C_11(self): return self.C_11
    def set_C_11(self, C_11): self.C_11 = C_11
    def get_C_10(self): return self.C_10
    def set_C_10(self, C_10): self.C_10 = C_10
    def get_C_1(self): return self.C_1
    def set_C_1(self, C_1): self.C_1 = C_1
    def get_C_3(self): return self.C_3
    def set_C_3(self, C_3): self.C_3 = C_3
    def get_C_2(self): return self.C_2
    def set_C_2(self, C_2): self.C_2 = C_2
    def get_C_5(self): return self.C_5
    def set_C_5(self, C_5): self.C_5 = C_5
    def get_C_4(self): return self.C_4
    def set_C_4(self, C_4): self.C_4 = C_4
    def get_C_7(self): return self.C_7
    def set_C_7(self, C_7): self.C_7 = C_7
    def get_C_6(self): return self.C_6
    def set_C_6(self, C_6): self.C_6 = C_6
    def get_C_9(self): return self.C_9
    def set_C_9(self, C_9): self.C_9 = C_9
    def get_C_8(self): return self.C_8
    def set_C_8(self, C_8): self.C_8 = C_8
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratCType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratCType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratCType'):
        if self.C_19 is not None and 'C_19' not in already_processed:
            already_processed.append('C_19')
            outfile.write(' C_19=%s' % (quote_attrib(self.C_19), ))
        if self.C_18 is not None and 'C_18' not in already_processed:
            already_processed.append('C_18')
            outfile.write(' C_18=%s' % (quote_attrib(self.C_18), ))
        if self.C_17 is not None and 'C_17' not in already_processed:
            already_processed.append('C_17')
            outfile.write(' C_17=%s' % (quote_attrib(self.C_17), ))
        if self.C_11 is not None and 'C_11' not in already_processed:
            already_processed.append('C_11')
            outfile.write(' C_11=%s' % (quote_attrib(self.C_11), ))
        if self.C_10 is not None and 'C_10' not in already_processed:
            already_processed.append('C_10')
            outfile.write(' C_10=%s' % (quote_attrib(self.C_10), ))
        outfile.write(' C_1=%s' % (quote_attrib(self.C_1), ))
        if self.C_3 is not None and 'C_3' not in already_processed:
            already_processed.append('C_3')
            outfile.write(' C_3=%s' % (quote_attrib(self.C_3), ))
        if self.C_2 is not None and 'C_2' not in already_processed:
            already_processed.append('C_2')
            outfile.write(' C_2=%s' % (quote_attrib(self.C_2), ))
        if self.C_5 is not None and 'C_5' not in already_processed:
            already_processed.append('C_5')
            outfile.write(' C_5=%s' % (quote_attrib(self.C_5), ))
        if self.C_4 is not None and 'C_4' not in already_processed:
            already_processed.append('C_4')
            outfile.write(' C_4=%s' % (quote_attrib(self.C_4), ))
        if self.C_7 is not None and 'C_7' not in already_processed:
            already_processed.append('C_7')
            outfile.write(' C_7=%s' % (quote_attrib(self.C_7), ))
        if self.C_6 is not None and 'C_6' not in already_processed:
            already_processed.append('C_6')
            outfile.write(' C_6=%s' % (quote_attrib(self.C_6), ))
        if self.C_9 is not None and 'C_9' not in already_processed:
            already_processed.append('C_9')
            outfile.write(' C_9=%s' % (quote_attrib(self.C_9), ))
        if self.C_8 is not None and 'C_8' not in already_processed:
            already_processed.append('C_8')
            outfile.write(' C_8=%s' % (quote_attrib(self.C_8), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratCType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratCType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.C_19 is not None and 'C_19' not in already_processed:
            already_processed.append('C_19')
            showIndent(outfile, level)
            outfile.write('C_19 = %s,\n' % (self.C_19,))
        if self.C_18 is not None and 'C_18' not in already_processed:
            already_processed.append('C_18')
            showIndent(outfile, level)
            outfile.write('C_18 = %s,\n' % (self.C_18,))
        if self.C_17 is not None and 'C_17' not in already_processed:
            already_processed.append('C_17')
            showIndent(outfile, level)
            outfile.write('C_17 = %s,\n' % (self.C_17,))
        if self.C_11 is not None and 'C_11' not in already_processed:
            already_processed.append('C_11')
            showIndent(outfile, level)
            outfile.write('C_11 = %s,\n' % (self.C_11,))
        if self.C_10 is not None and 'C_10' not in already_processed:
            already_processed.append('C_10')
            showIndent(outfile, level)
            outfile.write('C_10 = %s,\n' % (self.C_10,))
        if self.C_1 is not None and 'C_1' not in already_processed:
            already_processed.append('C_1')
            showIndent(outfile, level)
            outfile.write('C_1 = %s,\n' % (self.C_1,))
        if self.C_3 is not None and 'C_3' not in already_processed:
            already_processed.append('C_3')
            showIndent(outfile, level)
            outfile.write('C_3 = %s,\n' % (self.C_3,))
        if self.C_2 is not None and 'C_2' not in already_processed:
            already_processed.append('C_2')
            showIndent(outfile, level)
            outfile.write('C_2 = %s,\n' % (self.C_2,))
        if self.C_5 is not None and 'C_5' not in already_processed:
            already_processed.append('C_5')
            showIndent(outfile, level)
            outfile.write('C_5 = %s,\n' % (self.C_5,))
        if self.C_4 is not None and 'C_4' not in already_processed:
            already_processed.append('C_4')
            showIndent(outfile, level)
            outfile.write('C_4 = %s,\n' % (self.C_4,))
        if self.C_7 is not None and 'C_7' not in already_processed:
            already_processed.append('C_7')
            showIndent(outfile, level)
            outfile.write('C_7 = %s,\n' % (self.C_7,))
        if self.C_6 is not None and 'C_6' not in already_processed:
            already_processed.append('C_6')
            showIndent(outfile, level)
            outfile.write('C_6 = %s,\n' % (self.C_6,))
        if self.C_9 is not None and 'C_9' not in already_processed:
            already_processed.append('C_9')
            showIndent(outfile, level)
            outfile.write('C_9 = %s,\n' % (self.C_9,))
        if self.C_8 is not None and 'C_8' not in already_processed:
            already_processed.append('C_8')
            showIndent(outfile, level)
            outfile.write('C_8 = %s,\n' % (self.C_8,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('C_19')
        if value is not None and 'C_19' not in already_processed:
            already_processed.append('C_19')
            self.C_19 = value
        value = attrs.get('C_18')
        if value is not None and 'C_18' not in already_processed:
            already_processed.append('C_18')
            self.C_18 = value
        value = attrs.get('C_17')
        if value is not None and 'C_17' not in already_processed:
            already_processed.append('C_17')
            self.C_17 = value
        value = attrs.get('C_11')
        if value is not None and 'C_11' not in already_processed:
            already_processed.append('C_11')
            self.C_11 = value
        value = attrs.get('C_10')
        if value is not None and 'C_10' not in already_processed:
            already_processed.append('C_10')
            self.C_10 = value
        value = attrs.get('C_1')
        if value is not None and 'C_1' not in already_processed:
            already_processed.append('C_1')
            self.C_1 = value
        value = attrs.get('C_3')
        if value is not None and 'C_3' not in already_processed:
            already_processed.append('C_3')
            self.C_3 = value
        value = attrs.get('C_2')
        if value is not None and 'C_2' not in already_processed:
            already_processed.append('C_2')
            self.C_2 = value
        value = attrs.get('C_5')
        if value is not None and 'C_5' not in already_processed:
            already_processed.append('C_5')
            self.C_5 = value
        value = attrs.get('C_4')
        if value is not None and 'C_4' not in already_processed:
            already_processed.append('C_4')
            self.C_4 = value
        value = attrs.get('C_7')
        if value is not None and 'C_7' not in already_processed:
            already_processed.append('C_7')
            self.C_7 = value
        value = attrs.get('C_6')
        if value is not None and 'C_6' not in already_processed:
            already_processed.append('C_6')
            self.C_6 = value
        value = attrs.get('C_9')
        if value is not None and 'C_9' not in already_processed:
            already_processed.append('C_9')
            self.C_9 = value
        value = attrs.get('C_8')
        if value is not None and 'C_8' not in already_processed:
            already_processed.append('C_8')
            self.C_8 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratCType


class AsiguratDType(GeneratedsSuper):
    subclass = None
    superclass = None
    def __init__(self, D_20=None, D_16=None, D_8=None, D_9=None, D_18=None, D_19=None, D_2=None, D_3=None, D_15=None, D_1=None, D_6=None, D_7=None, D_4=None, D_5=None, D_14=None, D_21=None, D_12=None, D_13=None, D_11=None, D_10=None, D_17=None, valueOf_=None):
        self.D_20 = _cast(None, D_20)
        self.D_16 = _cast(None, D_16)
        self.D_8 = _cast(None, D_8)
        self.D_9 = _cast(None, D_9)
        self.D_18 = _cast(None, D_18)
        self.D_19 = _cast(float, D_19)
        self.D_2 = _cast(None, D_2)
        self.D_3 = _cast(None, D_3)
        self.D_15 = _cast(None, D_15)
        self.D_1 = _cast(None, D_1)
        self.D_6 = _cast(None, D_6)
        self.D_7 = _cast(None, D_7)
        self.D_4 = _cast(None, D_4)
        self.D_5 = _cast(None, D_5)
        self.D_14 = _cast(None, D_14)
        self.D_21 = _cast(None, D_21)
        self.D_12 = _cast(None, D_12)
        self.D_13 = _cast(None, D_13)
        self.D_11 = _cast(None, D_11)
        self.D_10 = _cast(None, D_10)
        self.D_17 = _cast(None, D_17)
        self.valueOf_ = valueOf_
    def factory(*args_, **kwargs_):
        if AsiguratDType.subclass:
            return AsiguratDType.subclass(*args_, **kwargs_)
        else:
            return AsiguratDType(*args_, **kwargs_)
    factory = staticmethod(factory)
    def get_D_20(self): return self.D_20
    def set_D_20(self, D_20): self.D_20 = D_20
    def get_D_16(self): return self.D_16
    def set_D_16(self, D_16): self.D_16 = D_16
    def get_D_8(self): return self.D_8
    def set_D_8(self, D_8): self.D_8 = D_8
    def get_D_9(self): return self.D_9
    def set_D_9(self, D_9): self.D_9 = D_9
    def get_D_18(self): return self.D_18
    def set_D_18(self, D_18): self.D_18 = D_18
    def get_D_19(self): return self.D_19
    def set_D_19(self, D_19): self.D_19 = D_19
    def get_D_2(self): return self.D_2
    def set_D_2(self, D_2): self.D_2 = D_2
    def get_D_3(self): return self.D_3
    def set_D_3(self, D_3): self.D_3 = D_3
    def get_D_15(self): return self.D_15
    def set_D_15(self, D_15): self.D_15 = D_15
    def get_D_1(self): return self.D_1
    def set_D_1(self, D_1): self.D_1 = D_1
    def get_D_6(self): return self.D_6
    def set_D_6(self, D_6): self.D_6 = D_6
    def get_D_7(self): return self.D_7
    def set_D_7(self, D_7): self.D_7 = D_7
    def get_D_4(self): return self.D_4
    def set_D_4(self, D_4): self.D_4 = D_4
    def get_D_5(self): return self.D_5
    def set_D_5(self, D_5): self.D_5 = D_5
    def get_D_14(self): return self.D_14
    def set_D_14(self, D_14): self.D_14 = D_14
    def get_D_21(self): return self.D_21
    def set_D_21(self, D_21): self.D_21 = D_21
    def get_D_12(self): return self.D_12
    def set_D_12(self, D_12): self.D_12 = D_12
    def get_D_13(self): return self.D_13
    def set_D_13(self, D_13): self.D_13 = D_13
    def get_D_11(self): return self.D_11
    def set_D_11(self, D_11): self.D_11 = D_11
    def get_D_10(self): return self.D_10
    def set_D_10(self, D_10): self.D_10 = D_10
    def get_D_17(self): return self.D_17
    def set_D_17(self, D_17): self.D_17 = D_17
    def get_valueOf_(self): return self.valueOf_
    def set_valueOf_(self, valueOf_): self.valueOf_ = valueOf_
    def export(self, outfile, level, namespace_='', name_='AsiguratDType', namespacedef_=''):
        showIndent(outfile, level)
        outfile.write('<%s%s%s' % (namespace_, name_, namespacedef_ and ' ' + namespacedef_ or '', ))
        self.exportAttributes(outfile, level, [], namespace_, name_='AsiguratDType')
        if self.hasContent_():
            outfile.write('>')
            outfile.write(self.valueOf_)
            self.exportChildren(outfile, level + 1, namespace_, name_)
            outfile.write('</%s%s>\n' % (namespace_, name_))
        else:
            outfile.write('/>\n')
    def exportAttributes(self, outfile, level, already_processed, namespace_='', name_='AsiguratDType'):
        if self.D_20 is not None and 'D_20' not in already_processed:
            already_processed.append('D_20')
            outfile.write(' D_20=%s' % (quote_attrib(self.D_20), ))
        if self.D_16 is not None and 'D_16' not in already_processed:
            already_processed.append('D_16')
            outfile.write(' D_16=%s' % (quote_attrib(self.D_16), ))
        if self.D_8 is not None and 'D_8' not in already_processed:
            already_processed.append('D_8')
            outfile.write(' D_8=%s' % (quote_attrib(self.D_8), ))
        outfile.write(' D_9=%s' % (quote_attrib(self.D_9), ))
        outfile.write(' D_18=%s' % (quote_attrib(self.D_18), ))
        outfile.write(' D_19="%s"' % self.gds_format_string(self.D_19, input_name='D_19'))
        outfile.write(' D_2=%s' % (self.gds_format_string(quote_attrib(self.D_2).encode(ExternalEncoding), input_name='D_2'), ))
        if self.D_3 is not None and 'D_3' not in already_processed:
            already_processed.append('D_3')
            outfile.write(' D_3=%s' % (self.gds_format_string(quote_attrib(self.D_3).encode(ExternalEncoding), input_name='D_3'), ))
        if self.D_15 is not None and 'D_15' not in already_processed:
            already_processed.append('D_15')
            outfile.write(' D_15=%s' % (quote_attrib(self.D_15), ))
        outfile.write(' D_1=%s' % (self.gds_format_string(quote_attrib(self.D_1).encode(ExternalEncoding), input_name='D_1'), ))
        outfile.write(' D_6=%s' % (quote_attrib(self.D_6), ))
        outfile.write(' D_7=%s' % (quote_attrib(self.D_7), ))
        if self.D_4 is not None and 'D_4' not in already_processed:
            already_processed.append('D_4')
            outfile.write(' D_4=%s' % (self.gds_format_string(quote_attrib(self.D_4).encode(ExternalEncoding), input_name='D_4'), ))
        outfile.write(' D_5=%s' % (quote_attrib(self.D_5), ))
        if self.D_14 is not None and 'D_14' not in already_processed:
            already_processed.append('D_14')
            outfile.write(' D_14=%s' % (quote_attrib(self.D_14), ))
        if self.D_21 is not None and 'D_21' not in already_processed:
            already_processed.append('D_21')
            outfile.write(' D_21=%s' % (quote_attrib(self.D_21), ))
        if self.D_12 is not None and 'D_12' not in already_processed:
            already_processed.append('D_12')
            outfile.write(' D_12=%s' % (quote_attrib(self.D_12), ))
        if self.D_13 is not None and 'D_13' not in already_processed:
            already_processed.append('D_13')
            outfile.write(' D_13=%s' % (self.gds_format_string(quote_attrib(self.D_13).encode(ExternalEncoding), input_name='D_13'), ))
        if self.D_11 is not None and 'D_11' not in already_processed:
            already_processed.append('D_11')
            outfile.write(' D_11=%s' % (quote_attrib(self.D_11), ))
        outfile.write(' D_10=%s' % (quote_attrib(self.D_10), ))
        outfile.write(' D_17=%s' % (quote_attrib(self.D_17), ))
    def exportChildren(self, outfile, level, namespace_='', name_='AsiguratDType'):
        pass
    def hasContent_(self):
        if (
            self.valueOf_
            ):
            return True
        else:
            return False
    def exportLiteral(self, outfile, level, name_='AsiguratDType'):
        level += 1
        self.exportLiteralAttributes(outfile, level, [], name_)
        if self.hasContent_():
            self.exportLiteralChildren(outfile, level, name_)
        showIndent(outfile, level)
        outfile.write('valueOf_ = """%s""",\n' % (self.valueOf_,))
    def exportLiteralAttributes(self, outfile, level, already_processed, name_):
        if self.D_20 is not None and 'D_20' not in already_processed:
            already_processed.append('D_20')
            showIndent(outfile, level)
            outfile.write('D_20 = %s,\n' % (self.D_20,))
        if self.D_16 is not None and 'D_16' not in already_processed:
            already_processed.append('D_16')
            showIndent(outfile, level)
            outfile.write('D_16 = %s,\n' % (self.D_16,))
        if self.D_8 is not None and 'D_8' not in already_processed:
            already_processed.append('D_8')
            showIndent(outfile, level)
            outfile.write('D_8 = %s,\n' % (self.D_8,))
        if self.D_9 is not None and 'D_9' not in already_processed:
            already_processed.append('D_9')
            showIndent(outfile, level)
            outfile.write('D_9 = %s,\n' % (self.D_9,))
        if self.D_18 is not None and 'D_18' not in already_processed:
            already_processed.append('D_18')
            showIndent(outfile, level)
            outfile.write('D_18 = %s,\n' % (self.D_18,))
        if self.D_19 is not None and 'D_19' not in already_processed:
            already_processed.append('D_19')
            showIndent(outfile, level)
            outfile.write('D_19 = %e,\n' % (self.D_19,))
        if self.D_2 is not None and 'D_2' not in already_processed:
            already_processed.append('D_2')
            showIndent(outfile, level)
            outfile.write('D_2 = "%s",\n' % (self.D_2,))
        if self.D_3 is not None and 'D_3' not in already_processed:
            already_processed.append('D_3')
            showIndent(outfile, level)
            outfile.write('D_3 = "%s",\n' % (self.D_3,))
        if self.D_15 is not None and 'D_15' not in already_processed:
            already_processed.append('D_15')
            showIndent(outfile, level)
            outfile.write('D_15 = %s,\n' % (self.D_15,))
        if self.D_1 is not None and 'D_1' not in already_processed:
            already_processed.append('D_1')
            showIndent(outfile, level)
            outfile.write('D_1 = "%s",\n' % (self.D_1,))
        if self.D_6 is not None and 'D_6' not in already_processed:
            already_processed.append('D_6')
            showIndent(outfile, level)
            outfile.write('D_6 = %s,\n' % (self.D_6,))
        if self.D_7 is not None and 'D_7' not in already_processed:
            already_processed.append('D_7')
            showIndent(outfile, level)
            outfile.write('D_7 = %s,\n' % (self.D_7,))
        if self.D_4 is not None and 'D_4' not in already_processed:
            already_processed.append('D_4')
            showIndent(outfile, level)
            outfile.write('D_4 = "%s",\n' % (self.D_4,))
        if self.D_5 is not None and 'D_5' not in already_processed:
            already_processed.append('D_5')
            showIndent(outfile, level)
            outfile.write('D_5 = %s,\n' % (self.D_5,))
        if self.D_14 is not None and 'D_14' not in already_processed:
            already_processed.append('D_14')
            showIndent(outfile, level)
            outfile.write('D_14 = %s,\n' % (self.D_14,))
        if self.D_21 is not None and 'D_21' not in already_processed:
            already_processed.append('D_21')
            showIndent(outfile, level)
            outfile.write('D_21 = %s,\n' % (self.D_21,))
        if self.D_12 is not None and 'D_12' not in already_processed:
            already_processed.append('D_12')
            showIndent(outfile, level)
            outfile.write('D_12 = %s,\n' % (self.D_12,))
        if self.D_13 is not None and 'D_13' not in already_processed:
            already_processed.append('D_13')
            showIndent(outfile, level)
            outfile.write('D_13 = "%s",\n' % (self.D_13,))
        if self.D_11 is not None and 'D_11' not in already_processed:
            already_processed.append('D_11')
            showIndent(outfile, level)
            outfile.write('D_11 = %s,\n' % (self.D_11,))
        if self.D_10 is not None and 'D_10' not in already_processed:
            already_processed.append('D_10')
            showIndent(outfile, level)
            outfile.write('D_10 = %s,\n' % (self.D_10,))
        if self.D_17 is not None and 'D_17' not in already_processed:
            already_processed.append('D_17')
            showIndent(outfile, level)
            outfile.write('D_17 = %s,\n' % (self.D_17,))
    def exportLiteralChildren(self, outfile, level, name_):
        pass
    def build(self, node):
        self.buildAttributes(node, node.attrib, [])
        self.valueOf_ = get_all_text_(node)
        for child in node:
            nodeName_ = Tag_pattern_.match(child.tag).groups()[-1]
            self.buildChildren(child, nodeName_)
    def buildAttributes(self, node, attrs, already_processed):
        value = attrs.get('D_20')
        if value is not None and 'D_20' not in already_processed:
            already_processed.append('D_20')
            self.D_20 = value
        value = attrs.get('D_16')
        if value is not None and 'D_16' not in already_processed:
            already_processed.append('D_16')
            self.D_16 = value
        value = attrs.get('D_8')
        if value is not None and 'D_8' not in already_processed:
            already_processed.append('D_8')
            self.D_8 = value
        value = attrs.get('D_9')
        if value is not None and 'D_9' not in already_processed:
            already_processed.append('D_9')
            self.D_9 = value
        value = attrs.get('D_18')
        if value is not None and 'D_18' not in already_processed:
            already_processed.append('D_18')
            self.D_18 = value
        value = attrs.get('D_19')
        if value is not None and 'D_19' not in already_processed:
            already_processed.append('D_19')
            try:
                self.D_19 = float(value)
            except ValueError, exp:
                raise ValueError('Bad float/double attribute (D_19): %s' % exp)
        value = attrs.get('D_2')
        if value is not None and 'D_2' not in already_processed:
            already_processed.append('D_2')
            self.D_2 = value
        value = attrs.get('D_3')
        if value is not None and 'D_3' not in already_processed:
            already_processed.append('D_3')
            self.D_3 = value
        value = attrs.get('D_15')
        if value is not None and 'D_15' not in already_processed:
            already_processed.append('D_15')
            self.D_15 = value
        value = attrs.get('D_1')
        if value is not None and 'D_1' not in already_processed:
            already_processed.append('D_1')
            self.D_1 = value
        value = attrs.get('D_6')
        if value is not None and 'D_6' not in already_processed:
            already_processed.append('D_6')
            self.D_6 = value
        value = attrs.get('D_7')
        if value is not None and 'D_7' not in already_processed:
            already_processed.append('D_7')
            self.D_7 = value
        value = attrs.get('D_4')
        if value is not None and 'D_4' not in already_processed:
            already_processed.append('D_4')
            self.D_4 = value
        value = attrs.get('D_5')
        if value is not None and 'D_5' not in already_processed:
            already_processed.append('D_5')
            self.D_5 = value
        value = attrs.get('D_14')
        if value is not None and 'D_14' not in already_processed:
            already_processed.append('D_14')
            self.D_14 = value
        value = attrs.get('D_21')
        if value is not None and 'D_21' not in already_processed:
            already_processed.append('D_21')
            self.D_21 = value
        value = attrs.get('D_12')
        if value is not None and 'D_12' not in already_processed:
            already_processed.append('D_12')
            self.D_12 = value
        value = attrs.get('D_13')
        if value is not None and 'D_13' not in already_processed:
            already_processed.append('D_13')
            self.D_13 = value
        value = attrs.get('D_11')
        if value is not None and 'D_11' not in already_processed:
            already_processed.append('D_11')
            self.D_11 = value
        value = attrs.get('D_10')
        if value is not None and 'D_10' not in already_processed:
            already_processed.append('D_10')
            self.D_10 = value
        value = attrs.get('D_17')
        if value is not None and 'D_17' not in already_processed:
            already_processed.append('D_17')
            self.D_17 = value
    def buildChildren(self, child_, nodeName_, from_subclass=False):
        pass
# end class AsiguratDType


USAGE_TEXT = """
Usage: python <Parser>.py [ -s ] <in_xml_file>
"""

def usage():
    print USAGE_TEXT
    sys.exit(1)


def get_root_tag(node):
    tag = Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = globals().get(tag)
    return tag, rootClass


def parse(inFileName):
    doc = parsexml_(inFileName)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'declaratieUnica'
        rootClass = declaratieUnica
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag, 
        namespacedef_='')
    return rootObj


def parseString(inString):
    from StringIO import StringIO
    doc = parsexml_(StringIO(inString))
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'declaratieUnica'
        rootClass = declaratieUnica
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_="declaratieUnica",
        namespacedef_='')
    return rootObj


def parseLiteral(inFileName):
    doc = parsexml_(inFileName)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'declaratieUnica'
        rootClass = declaratieUnica
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('#from D112 import *\n\n')
    sys.stdout.write('import D112 as model_\n\n')
    sys.stdout.write('rootObj = model_.rootTag(\n')
    rootObj.exportLiteral(sys.stdout, 0, name_=rootTag)
    sys.stdout.write(')\n')
    return rootObj


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        parse(args[0])
    else:
        usage()


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()


__all__ = [
    "AngajatorAType",
    "AngajatorBType",
    "AngajatorC1Type",
    "AngajatorC2Type",
    "AngajatorC3Type",
    "AngajatorC4Type",
    "AngajatorC5Type",
    "AngajatorC6Type",
    "AngajatorC7Type",
    "AngajatorDType",
    "AngajatorE1Type",
    "AngajatorE2Type",
    "AngajatorE3Type",
    "AngajatorE4Type",
    "AngajatorF1Type",
    "AngajatorF2Type",
    "AngajatorType",
    "AsiguratAType",
    "AsiguratB11Type",
    "AsiguratB1Type",
    "AsiguratB2Type",
    "AsiguratB3Type",
    "AsiguratB4Type",
    "AsiguratCType",
    "AsiguratDType",
    "AsiguratType",
    "CoAsiguratiType",
    "declaratieUnica"
    ]
