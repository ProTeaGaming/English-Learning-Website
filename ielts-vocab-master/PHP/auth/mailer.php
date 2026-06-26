<?php
function get_mail_config(): ?array {
    $path = __DIR__ . '/config.local.php';
    if (!file_exists($path)) return null;
    return require $path;
}

function smtp_read($socket): string {
    $data = '';
    while (($line = fgets($socket, 515)) !== false) {
        $data .= $line;
        if (isset($line[3]) && $line[3] === ' ') break;
    }
    return $data;
}

function smtp_send_mail(string $to, string $subject, string $bodyText): bool {
    $config = get_mail_config();
    if (!$config) {
        error_log('Mailer: auth/config.local.php is missing, cannot send email.');
        return false;
    }

    $socket = @stream_socket_client(
        'tcp://' . $config['smtp_host'] . ':' . $config['smtp_port'],
        $errno, $errstr, 15
    );
    if (!$socket) {
        error_log("Mailer: connection failed: $errstr");
        return false;
    }

    smtp_read($socket);
    fwrite($socket, "EHLO localhost\r\n");
    smtp_read($socket);

    fwrite($socket, "STARTTLS\r\n");
    smtp_read($socket);
    if (!stream_socket_enable_crypto($socket, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
        error_log('Mailer: TLS negotiation failed');
        fclose($socket);
        return false;
    }

    fwrite($socket, "EHLO localhost\r\n");
    smtp_read($socket);

    fwrite($socket, "AUTH LOGIN\r\n");
    smtp_read($socket);
    fwrite($socket, base64_encode($config['smtp_user']) . "\r\n");
    smtp_read($socket);
    fwrite($socket, base64_encode($config['smtp_pass']) . "\r\n");
    $authResp = smtp_read($socket);
    if (strpos($authResp, '235') !== 0) {
        error_log("Mailer: auth failed: $authResp");
        fclose($socket);
        return false;
    }

    fwrite($socket, "MAIL FROM:<{$config['from_email']}>\r\n");
    smtp_read($socket);
    fwrite($socket, "RCPT TO:<{$to}>\r\n");
    smtp_read($socket);
    fwrite($socket, "DATA\r\n");
    smtp_read($socket);

    $headers  = "From: {$config['from_name']} <{$config['from_email']}>\r\n";
    $headers .= "To: <{$to}>\r\n";
    $headers .= "Subject: {$subject}\r\n";
    $headers .= "MIME-Version: 1.0\r\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

    $escapedBody = preg_replace('/^\./m', '..', $bodyText);
    fwrite($socket, $headers . "\r\n" . $escapedBody . "\r\n.\r\n");
    smtp_read($socket);

    fwrite($socket, "QUIT\r\n");
    smtp_read($socket);
    fclose($socket);

    return true;
}
