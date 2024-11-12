from platform import processor

import cson
import os
import json
import shutil
import re
import uuid


class Processor:
    def __init__(self, source_folder, out_folder):
        self.sourceFolder = source_folder
        self.outFolder = out_folder
        self.attachmentRegex = re.compile(r"(.*?!\[)(.*)(\]\(:storage[\/\\])(.*)([\/\\])(.*\.(png|gif|jpg|jpeg))(\))", flags=re.IGNORECASE)
        self.file_name_count = 0

    def setup_obsidian_settings(self):
        target_settings_directory = os.path.join(self.outFolder, ".obsidian")
        if not os.path.exists(target_settings_directory):
            os.makedirs(target_settings_directory)
        source_config_dir = os.path.abspath(os.path.join(__file__, os.pardir, "default_configuration", ".obsidian"))
        for file in os.listdir(source_config_dir):
            source_file = os.path.join(source_config_dir, file)
            target_file = os.path.join(target_settings_directory, file)
            shutil.copyfile(source_file, target_file)


    def load_folder_mappings(self):
        folder_mappings = os.path.join(self.sourceFolder, "boostnote.json")
        folder_mappings = json.load(open(folder_mappings, "r"))
        folder_mappings = {item["key"]: item["name"] for item in folder_mappings["folders"]}
        # print(folder_mappings)
        return folder_mappings


    @staticmethod
    def load_note(file_path, folder_mappings):
        stream = open(file_path, "rb")
        data = cson.load(stream)
        if data["type"] == "MARKDOWN_NOTE":
            # print("Markdown")
            # print("content: ", data['content'][:5] + "...")
            # print("folderKey: ", data['folder'])
            # print("folderName: ", folder_mappings[data['folder']])
            # print("title: ", data['title'][5:] + "...")
            note = {
                "folderName": folder_mappings[data['folder']].replace(" ", "_"),
                "title": data['title'],
                "content": data['content']
            }
            return note

        elif data["type"] == "SNIPPET_NOTE":
            # print("Snippet")
            # print("\tfolderKey: ", data['folder'])
            # print("\tfolderName: ", folder_mappings[data['folder']])
            # print("\ttitle: ", data['title'])
            # print("\tsnippets[0].content: ", data["snippets"][0]['content'])
            # print()
            note = {
                "folderName": folder_mappings[data['folder']].replace(" ", "_"),
                "title": data['title'],
                "content": data["snippets"][0]['content']
            }
            return note

    def convert_to_obsidian(self, note):
        out_folder = os.path.join(self.outFolder, note["folderName"])
        if os.path.exists(out_folder) is False:
            os.mkdir(out_folder)

        content = note["content"]
        print(len([line for line in content.split("\n") if ":storage" in line.lower()]))
        lines = content.split("\n")
        new_lines = []
        for i in range(len(lines)):
            line = lines[i]
            if ":storage" in line:
                print(line)
                match = self.attachmentRegex.match(line)
                output_attachments_folder = os.path.join(out_folder, "attachments")
                if os.path.exists(output_attachments_folder) is False:
                    os.mkdir(output_attachments_folder)
                alt_text = match.group(2)
                parent_folder = match.group(4)
                image_file = match.group(6)
                extension = image_file.split(".")[1]
                uuid_file_name = '%s.%s' % (str(uuid.uuid4()), extension)
                src_attachment_path = os.path.join(self.sourceFolder, "attachments", parent_folder, image_file)
                new_image_path = os.path.join(output_attachments_folder, uuid_file_name)
                shutil.copyfile(src_attachment_path, new_image_path)
                new_line = '![%s](%s/attachments/%s)' % (alt_text, note["folderName"], uuid_file_name)
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        note_title = note["title"].replace(":", " ")
        if len(note_title) > 290:
            print("TITLE IS TOO LONG!")
            note_title = note["folderName"] + str(self.file_name_count)
            self.file_name_count += 1
        note_out_path = os.path.join(out_folder, "%s.md" % note_title)
        open(note_out_path, "w", encoding='utf-8').write("\n".join(new_lines))

    def run(self):
        self.setup_obsidian_settings()
        folder_mappings = self.load_folder_mappings()
        note_paths = [os.path.join(self.sourceFolder, "notes", file) for file in os.listdir(os.path.join(self.sourceFolder, "notes")) if ".cson" in file]
        notes = [self.load_note(path, folder_mappings) for path in note_paths]
        [self.convert_to_obsidian(note) for note in notes]



if __name__ == "__main__":
    boostNotSrc = "C:\\Users\\alimi\\git_repos\\BoostNotes"
    obsidianDst = "C:\\Users\\alimi\\git_repos\\ObsidianVault"
    processor = Processor(boostNotSrc, obsidianDst)
    processor.run()
