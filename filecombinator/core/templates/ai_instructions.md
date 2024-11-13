# Instructions for AI Assistant

**Dear AI Assistant,**

You are about to process a document generated by **FileCombinator**, which contains the combined contents of multiple files from a project. The document is formatted in **Markdown** and includes the directory structure, file metadata, and file contents. Your task is to accurately interpret and process this document to build a comprehensive understanding of the project's structure and contents.

## Guidelines for Processing the Document

- **Overall Structure**:

  - The document begins with the **Directory Structure**, represented as a tree diagram enclosed within code blocks using **five backticks** (`````) and specified as `plaintext`.

  - Following the directory structure, each **File Section** starts with a second-level header (`##`) that includes the file path.

  - Under each file header, **Metadata** is provided as a bullet-point list.

  - The content of each file is enclosed within code blocks using **five backticks** (`````), with the appropriate language specified for syntax highlighting.

- **Parsing the Directory Structure**:

  - Locate the directory tree diagram enclosed in code blocks with `plaintext`.

  - Use the indentation and line-drawing characters (`├──`, `│`, `└──`) to understand the hierarchical relationships between directories and files.

- **Extracting File Metadata**:

  - For each file section, extract the metadata listed under the **Metadata** heading.

  - Metadata includes:

    - **Type**: The file type (e.g., Text, Binary, Image).

    - **Size**: The size of the file in bytes.

    - **Last Modified**: The timestamp of the last modification.

- **Processing File Content**:

  - **Code and Text Files**:

    - Identify code blocks enclosed with five backticks (`````).

    - Use the language specifier provided after the opening backticks to apply appropriate syntax highlighting and parsing rules.

    - Preserve all code, comments, and formatting exactly as they appear.

  - **Markdown Files**:

    - Treat files with the `markdown` language specifier appropriately, rendering any Markdown syntax within the content.

  - **Binary and Image Files**:

    - Recognize that for files of type **Binary** or **Image**, the content is not included.

    - A placeholder message (*Content excluded: Binary file* or *Content excluded: Image file*) is provided instead.

    - Use the metadata to acknowledge the existence and properties of these files.

- **Understanding Section Separators**:

  - A horizontal rule (`---`) is used to separate different file sections.

  - Use these separators to delineate the start and end of each file's information.

- **Important Considerations**:

  - **Consistent Delimiters**:

    - The use of five backticks (`````) for code blocks is consistent throughout the document to avoid conflicts with any content that may contain triple backticks or triple quotes.

  - **Language Specifiers**:

    - Common language specifiers include `python`, `javascript`, `text`, `markdown`, `plaintext`, etc.

    - Use the language specifier to guide your parsing and understanding of the code blocks.

  - **Content Integrity**:

    - Do not modify the content of the files during processing.

    - Maintain the original formatting, including indentation and line breaks.

  - **Error Handling**:

    - If you encounter any unexpected formatting or content, attempt to recover gracefully without skipping important information.

    - Pay special attention to files that might contain sequences resembling the delimiters.

- **Objectives**:

  - Build a detailed internal representation of the project's structure, including the relationships between files and directories.

  - Accurately extract and interpret the content of code and text files for further analysis.

  - Recognize and acknowledge binary and image files through their metadata.

**Thank you for following these instructions. You may now proceed to process the document starting with the Directory Structure below.**

---