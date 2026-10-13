<?php
/**
 * Proxy PHP pentru lista de participanti.
 * Inlocuieste endpoint-ul Flask /api/participants.
 * Parseaza pagina racetime.ro si returneaza datele ca JSON.
 */

header('Content-Type: application/json; charset=utf-8');

$url = 'https://racetime.ro/events/189/participants';

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 15);
curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

$response = curl_exec($ch);

if ($response === false) {
    http_response_code(502);
    echo json_encode([
        'error' => 'Nu s-a putut încărca lista de participanți.',
    ]);
    exit;
}

curl_close($ch);

$doc = new DOMDocument();
libxml_use_internal_errors(true);
$doc->loadHTML($response);
libxml_clear_errors();

$table = $doc->getElementsByTagName('table')->item(0);
if (!$table) {
    echo json_encode(['participants' => [], 'count' => 0]);
    exit;
}

$tbody = $table->getElementsByTagName('tbody')->item(0);
$rows = $tbody ? $tbody->getElementsByTagName('tr') : $table->getElementsByTagName('tr');

function getElementText($node, $default = '') {
    return $node ? trim($node->textContent) : $default;
}

$participants = [];

foreach ($rows as $row) {
    $cells = $row->getElementsByTagName('td');
    if ($cells->length === 0) {
        continue;
    }

    $cellTexts = [];
    foreach ($cells as $cell) {
        $cellTexts[] = trim($cell->textContent);
    }

    $text = implode(' ', $cellTexts);
    if (strpos($text, 'Nu au fost găsiți participanți') !== false) {
        continue;
    }

    if ($cells->length >= 5) {
        $raceCell = $cells->item(0);
        $raceNameEl = null;
        $raceCategoryEl = null;
        foreach ($raceCell->getElementsByTagName('div') as $div) {
            $class = $div->getAttribute('class');
            if (strpos($class, 'font-semibold') !== false) {
                $raceNameEl = $div;
            } elseif (strpos($class, 'text-xs') !== false && strpos($class, 'italic') !== false) {
                $raceCategoryEl = $div;
            }
        }
        $raceName = getElementText($raceNameEl);
        $raceCategory = getElementText($raceCategoryEl);

        $cityCell = $cells->item(3);
        $countryEl = null;
        foreach ($cityCell->getElementsByTagName('p') as $p) {
            if (strpos($p->getAttribute('class'), 'text-xs') !== false) {
                $countryEl = $p;
                break;
            }
        }
        $country = getElementText($countryEl);
        if ($countryEl) {
            $cityCell->removeChild($countryEl);
        }
        $city = getElementText($cityCell);

        $participants[] = [
            'race'       => $raceName,
            'category'   => $raceCategory,
            'last_name'  => $cellTexts[1],
            'first_name' => $cellTexts[2],
            'city'       => $city,
            'country'    => $country,
            'club'       => $cellTexts[4],
            'status'     => $cellTexts[5] ?? '',
        ];
    } else {
        $participants[] = [
            'race'       => '',
            'category'   => '',
            'last_name'  => '',
            'first_name' => $text,
            'city'       => '',
            'country'    => '',
            'club'       => '',
            'status'     => '',
        ];
    }
}

header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Expires: 0');

echo json_encode([
    'participants' => $participants,
    'count'        => count($participants),
]);
