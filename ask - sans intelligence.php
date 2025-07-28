<?php
// ask.php

header('Content-Type: application/json');
header("Access-Control-Allow-Origin: *");

// Charger la base de connaissance
$faq = json_decode(file_get_contents('faq.json'), true);

// Lire la phrase envoyée
$data = json_decode(file_get_contents('php://input'), true);
$userMessage = strtolower(trim($data['message'] ?? ''));

if (!$userMessage) {
    echo json_encode(['answer' => "Veuillez poser une question.", 'confidence' => 0]);
    exit;
}

// Fonction de similarité
function getSimilarityScore($a, $b) {
    similar_text($a, $b, $percent);
    return $percent; // % de similarité
}

$bestMatch = null;
$highestScore = 0;

foreach ($faq as $item) {
    $score = getSimilarityScore(strtolower($item['question']), $userMessage);
    if ($score > $highestScore) {
        $highestScore = $score;
        $bestMatch = $item;
    }
}

// Seuil minimal de confiance
$threshold = 60;

if ($highestScore >= $threshold) {
    echo json_encode([
        'answer' => $bestMatch['answer'],
        'confidence' => round($highestScore / 100, 2)
    ]);
} else {
    // Log la question incomprise
    $logEntry = date('Y-m-d H:i:s') . " - " . $userMessage . PHP_EOL;
    file_put_contents('unmatched_questions.log', $logEntry, FILE_APPEND);

    // Réponse par défaut
    echo json_encode([
        'answer' => "Je n’ai pas bien compris votre question. Pouvez-vous reformuler ou contacter un opérateur ?",
        'confidence' => 0
    ]);
}
