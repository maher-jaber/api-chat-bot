<?php
header('Content-Type: application/json; charset=utf-8');
header("Access-Control-Allow-Origin: *");

$data = json_decode(file_get_contents('php://input'), true);
$userMessage = trim($data['message'] ?? '');

if (!$userMessage) {
    echo json_encode(['answer' => "Veuillez poser une question.", 'confidence' => 0]);
    exit;
}

// Échapper les caractères dangereux
$escapedMessage = escapeshellarg($userMessage);

// Appeler Python
$command = "python answer.py $escapedMessage";
$output = shell_exec($command);

// Erreur ?
if (!$output) {
    echo json_encode(['answer' => "Erreur interne de traitement.", 'confidence' => 0]);
    exit;
}

// Retourner la réponse
echo $output;
