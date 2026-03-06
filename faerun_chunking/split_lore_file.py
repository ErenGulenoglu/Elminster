import os
import re

def count_words(text):
    """Count words in a text string."""
    return len(text.split())

def split_into_paragraphs(text):
    """Split text into paragraphs, removing empty ones."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs

def split_large_paragraph(paragraph, max_words=150):
    """Split a large paragraph into smaller chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
    chunks = []
    current_chunk = []
    current_words = 0
    
    for sentence in sentences:
        sentence_words = count_words(sentence)
        
        if current_words + sentence_words > max_words and current_chunk:
            # Save current chunk and start new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_words = sentence_words
        else:
            current_chunk.append(sentence)
            current_words += sentence_words
    
    # Add remaining sentences
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def create_chunks(text, min_words=200, max_words=500):
    """
    Create optimally-sized chunks from text.
    
    Args:
        text: Input text to chunk
        min_words: Minimum words per chunk (default 200)
        max_words: Maximum words per chunk (default 500)
    
    Returns:
        List of text chunks
    """
    chunks = []
    
    # First, split by major sections (headers like === Description ===)
    sections = re.split(r'(===\s+[^=]+\s+===)', text)
    
    current_chunk = ""
    current_words = 0
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        section_words = count_words(section)
        
        # If it's a header, keep it with the following content
        if section.strip().startswith('==='):
            # Save current chunk if it exists
            if current_chunk and current_words >= min_words:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_words = 0
            
            current_chunk = section + "\n"
            current_words = section_words
            
        else:
            # Process content section
            paragraphs = split_into_paragraphs(section)
            
            for para in paragraphs:
                para_words = count_words(para)
                
                # If paragraph is too large, split it
                if para_words > 150:
                    para_chunks = split_large_paragraph(para, max_words=150)
                    for pc in para_chunks:
                        pc_words = count_words(pc)
                        
                        if current_words + pc_words > max_words:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = pc + "\n\n"
                            current_words = pc_words
                        else:
                            current_chunk += pc + "\n\n"
                            current_words += pc_words
                else:
                    # Check if adding this paragraph would exceed max_words
                    if current_words + para_words > max_words and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = para + "\n\n"
                        current_words = para_words
                    else:
                        current_chunk += para + "\n\n"
                        current_words += para_words
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def save_chunks(chunks, output_dir, base_filename):
    """Save chunks to individual files."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, chunk in enumerate(chunks, 1):
        output_filename = f"{base_filename}_chunk_{i:03d}.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        word_count = count_words(chunk)
        print(f"Created {output_filename} ({word_count} words)")

def process_file(input_file, output_dir, min_words=200, max_words=500):
    """Process a single file and split it into chunks."""
    print(f"\nProcessing: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    total_words = count_words(text)
    print(f"Total words in original file: {total_words}")
    
    # Create chunks
    chunks = create_chunks(text, min_words, max_words)
    
    # Get base filename without extension
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    
    # Save chunks
    save_chunks(chunks, output_dir, base_filename)
    
    print(f"\nCreated {len(chunks)} chunks")
    print(f"Average words per chunk: {total_words / len(chunks):.1f}")

    print("\n" + "=" * 60)
    print("DONE! Chunks saved to:", output_dir)
    print("=" * 60)

# Example usage
if __name__ == "__main__":
    # Process the uploaded file
    
    # process_file(input_file, output_dir, min_words=200, max_words=500)
    process_file(f"./pdf_reader/Output/The Making of a Mage.pdf.txt", f"./lore_chunks/The Making of a Mage", min_words=200, max_words=500)
    

