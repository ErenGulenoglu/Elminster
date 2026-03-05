/**
 * Splits Elminster's response into readable paragraphs.
 *
 * Strategy:
 * 1. Split on existing newlines first (if the model ever uses them)
 * 2. For chunks that are still very long, break on sentence boundaries
 *    every ~400 chars so no single visual block overwhelms the reader
 */
export function formatElminsterResponse(text: string): string[] {
    // Normalise line endings, trim
    const cleaned = text.replace(/\r\n/g, "\n").trim();

    // Split on one or more blank lines first
    const rawChunks = cleaned.split(/\n{2,}/);

    const paragraphs: string[] = [];

    for (const chunk of rawChunks) {
        const trimmed = chunk.replace(/\n/g, " ").trim();
        if (!trimmed) continue;

        // If the chunk is short enough, keep it whole
        if (trimmed.length <= 420) {
            paragraphs.push(trimmed);
            continue;
        }

        // Otherwise break on sentence endings every ~400 chars
        const sentences = trimmed.match(/[^.!?]+[.!?]+["']?\s*/g) ?? [trimmed];
        let current = "";

        for (const sentence of sentences) {
            if ((current + sentence).length > 420 && current.length > 0) {
                paragraphs.push(current.trim());
                current = sentence;
            } else {
                current += sentence;
            }
        }

        if (current.trim()) paragraphs.push(current.trim());
    }

    return paragraphs.length > 0 ? paragraphs : [cleaned];
}
