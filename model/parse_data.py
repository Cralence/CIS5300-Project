import xml.etree.ElementTree as ET
from tqdm import tqdm
import os


def has_numeric(s):
    for c in s:
        if c.isnumeric():
            return True
    return False


def parse_data_base(source_data_list: list, parsed_res_list: list):
    for i in tqdm(range(len(source_data_list)), desc='Parsing'):
        file = source_data_list[i]
        try:
            tree = ET.parse("data/top1000_complete/" + file + "/Documents_xml/" + file + ".xml")
            root = tree.getroot()
            xmlstr = " ".join([elem.text for elem in root.findall('.//S') if elem.text is not None])

            summary = open('data/top1000_complete/' + file + "/summary/" + file + ".gold.txt", 'r')
            summary_str = summary.read()
            summary.close()

            parsed_res_list.append([summary_str, xmlstr])
        except:
            pass


def parse_data_improved(source_data_list: list, parsed_res_list: list, max_sentence_per_sec):
    for i in tqdm(range(len(source_data_list)), desc='Parsing data'):
        file = source_data_list[i]
        xml_path = os.path.join('data/top1000_complete', file, 'Documents_xml', file + '.xml')
        if not os.path.exists(xml_path):
            continue
        tree = ET.parse(xml_path)
        root = tree.getroot()

        text = []
        # find the title
        title_element = root.find(".//S[@sid='0']")
        if title_element is not None and title_element.text is not None:
            text.append(title_element.text.strip() + '\n')
        # traverse each section
        for child in root:
            if child.tag == 'ABSTRACT':
                # add all sentences in abstract
                for sub_child in child:
                    text.append(sub_child.text + '\n')
            elif child.tag == 'SECTION':
                section_title = child.attrib['title'].lower()
                if 'intro' in section_title:
                    # add all sentences in intro section
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                elif 'conclusion' in section_title:
                    # add all sentences in conclusion section
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                elif 'acknowledgement' in section_title:
                    # do not include anything in acknowledgement
                    continue
                elif section_title == '' and child.attrib['number'] == '1':
                    # on observation, these paragraphs are also important, just include all
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                else:
                    # include the first few sentences only
                    count = 0
                    child_it = iter(child)
                    while count < max_sentence_per_sec:
                        try:
                            sent = next(child_it)
                            text.append(sent.text + '\n')
                            count += 1
                        except StopIteration:
                            break
            elif child.tag == 'S':  # special case that there is no 'abstract', 'intro' ... structures in the file,
                # so just add all sentences
                if child.attrib['sid'] == '0':
                    # title has already been added, just skip
                    continue
                if child.text is not None:
                    text.append(child.text + '\n')

        # filter out noisy sentences
        selected_text = []
        for i_sent, sent in enumerate(text):
            n_word = len(sent.split(' '))
            if n_word > 50:  # too many numbers
                if sum([has_numeric(w) for w in sent.split(' ')]) / n_word > 0.15:
                    continue
            if n_word <= 4:  # too short
                if i_sent != 0:
                    continue
            if n_word > 30:  # too many symbols/incomplete words
                if sum([len(w) <= 2 for w in sent.split(' ')]) / n_word > 0.4:
                    continue
            if n_word > 20:  # contains too many '/'
                if sum([('/' in w) for w in sent.split(' ')]) / n_word > 0.2:
                    continue
            if sent in selected_text:  # remove duplicated sentences
                continue
            selected_text.append(sent)

        final_text = ''.join(selected_text)
        final_text = 'summarize: ' + f'\"{final_text}\"'

        summary = open('data/top1000_complete/' + file + "/summary/" + file + ".gold.txt", 'rb')
        summary_str = summary.read()
        summary_str = summary_str.decode('utf-8')
        summary.close()

        parsed_res_list.append([summary_str, final_text])


def parse_data_longT5(source_data_list: list, parsed_res_list: list, max_sentence_per_sec):
    # This differs from parse_data_improved that it does not add a prefix of 'summarize: '
    for i in tqdm(range(len(source_data_list)), desc='Parsing data'):
        file = source_data_list[i]
        xml_path = os.path.join('data/top1000_complete', file, 'Documents_xml', file + '.xml')
        if not os.path.exists(xml_path):
            continue
        tree = ET.parse(xml_path)
        root = tree.getroot()

        text = []
        # find the title
        title_element = root.find(".//S[@sid='0']")
        if title_element is not None and title_element.text is not None:
            text.append(title_element.text.strip() + '\n')
        # traverse each section
        for child in root:
            if child.tag == 'ABSTRACT':
                # add all sentences in abstract
                for sub_child in child:
                    text.append(sub_child.text + '\n')
            elif child.tag == 'SECTION':
                section_title = child.attrib['title'].lower()
                if 'intro' in section_title:
                    # add all sentences in intro section
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                elif 'conclusion' in section_title:
                    # add all sentences in conclusion section
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                elif 'acknowledgement' in section_title:
                    # do not include anything in acknowledgement
                    continue
                elif section_title == '' and child.attrib['number'] == '1':
                    # on observation, these paragraphs are also important, just include all
                    for sub_child in child:
                        text.append(sub_child.text + '\n')
                else:
                    # include the first few sentences only
                    count = 0
                    child_it = iter(child)
                    while count < max_sentence_per_sec:
                        try:
                            sent = next(child_it)
                            text.append(sent.text + '\n')
                            count += 1
                        except StopIteration:
                            break
            elif child.tag == 'S':  # special case that there is no 'abstract', 'intro' ... structures in the file,
                # so just add all sentences
                if child.attrib['sid'] == '0':
                    # title has already been added, just skip
                    continue
                if child.text is not None:
                    text.append(child.text + '\n')

        # filter out noisy sentences
        selected_text = []
        for i_sent, sent in enumerate(text):
            n_word = len(sent.split(' '))
            if n_word > 50:  # too many numbers
                if sum([has_numeric(w) for w in sent.split(' ')]) / n_word > 0.15:
                    continue
            if n_word <= 4:  # too short
                if i_sent != 0:
                    continue
            if n_word > 30:  # too many symbols/incomplete words
                if sum([len(w) <= 2 for w in sent.split(' ')]) / n_word > 0.4:
                    continue
            if n_word > 20:  # contains too many '/'
                if sum([('/' in w) for w in sent.split(' ')]) / n_word > 0.2:
                    continue
            if sent in selected_text:  # remove duplicated sentences
                continue
            selected_text.append(sent)

        final_text = ''.join(selected_text)

        summary = open('data/top1000_complete/' + file + "/summary/" + file + ".gold.txt", 'rb')
        summary_str = summary.read()
        summary_str = summary_str.decode('utf-8')
        summary.close()

        parsed_res_list.append([summary_str, final_text])
