<?php

$api_url = 'http://localhost:5000/recommend-id'; 


// emzai gửi array của mấy thằng enrolled nhé
$data = array(1801, 1, 3356);

$json_data = json_encode($data);

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $api_url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $json_data);
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);

curl_close($ch);

// nó response lại theo array 
echo $response;
?>
