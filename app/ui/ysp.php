<?php
date_default_timezone_set('Asia/Shanghai');
// CLI模式兼容：把命令行参数解析到$_GET（php -f ysp.php id=cctv1 playseek=...）
if (php_sapi_name() === 'cli' && isset($argv)) {
    parse_str(implode('&', array_slice($argv, 1)), $_GET);
}
$id = isset($_GET['id']) ? $_GET['id'] : 'cctv1';
$n = [
    'cctv1' => ['2024078201', '600001859', 'fhd'], //CCTV-1高清
    'cctv2' => ['2024075401', '600001800', 'fhd'], //CCTV-2高清
    'cctv3' => ['2024068501', '600001801', 'fhd'], //CCTV-3高清
    'cctv4' => ['2029797101', '600001814', 'fhd'], //CCTV-4高清
    'cctv5' => ['2024078401', '600001818', 'fhd'], //CCTV-5高清
    'cctv5p' => ['2024078001', '600001817', 'fhd'], //CCTV-5+高清
    'cctv6' => ['2013693901', '600108442', 'fhd'], //CCTV-6高清
    'cctv7' => ['2024072001', '600004092', 'fhd'], //CCTV-7高清
    'cctv8' => ['2029793001', '600001803', 'fhd'], //CCTV-8高清
    'cctv9' => ['2024078601', '600004078', 'fhd'], //CCTV-9高清
    'cctv10' => ['2024078701', '600001805', 'fhd'], //CCTV-10高清
    'cctv11' => ['2027248701', '600001806', 'fhd'], //CCTV-11高清
    'cctv12' => ['2027248801', '600001807', 'fhd'], //CCTV-12高清
    'cctv13' => ['2029797201', '600001811', 'fhd'], //CCTV-13高清
    'cctv14' => ['2027248901', '600001809', 'fhd'], //CCTV-14高清
    'cctv15' => ['2027249001', '600001815', 'fhd'], //CCTV-15高清
    'cctv16' => ['2027249101', '600098637', 'fhd'], //CCTV-16高清
    'cctv164k' => ['2027249301', '600099502', 'fhd'], //CCTV-16(4K)
    'cctv17' => ['2027249401', '600001810', 'fhd'], //CCTV-17高清
    'cctv4k' => ['2029810301', '600002264', 'fhd'], //CCTV-4K
    'cctv8k' => ['2026774101', '600156816', 'fhd'], //CCTV-8K
    'cgtn' => ['2024181701', '600014550', 'fhd'], //CGTN
    'cgtnfy' => ['2024181801', '600084704', 'fhd'], //CGTN法语频道
    'cgtney' => ['2024181901', '600084758', 'fhd'], //CGTN俄语频道
    'cgtnalby' => ['2024182001', '600084782', 'fhd'], //CGTN阿拉伯语频道
    'cgtnxby' => ['2024182101', '600084744', 'fhd'], //CGTN西班牙语频道
    'cgtnwyjl' => ['2024182301', '600084781', 'fhd'], //CGTN外语纪录频道
    'cctvfyjc' => ['2025637103', '600099658', 'shd'], //CCTV风云剧场频道
    'cctvdyjc' => ['2026874203', '600099655', 'shd'], //CCTV第一剧场频道
    'cctvhjjc' => ['2026874303', '600099620', 'shd'], //CCTV怀旧剧场频道
    'cctvsjdl' => ['2026874403', '600099637', 'shd'], //CCTV世界地理频道
    'cctvfyyy' => ['2026874503', '600099660', 'shd'], //CCTV风云音乐频道
    'cctvbqkj' => ['2026874603', '600099649', 'shd'], //CCTV兵器科技频道
    'cctvfyzq' => ['2026966203', '600099636', 'shd'], //CCTV风云足球频道
    'cctvgeqwq' => ['2026874703', '600099659', 'shd'], //CCTV高尔夫·网球频道
    'cctvnxss' => ['2026874803', '600099650', 'shd'], //CCTV女性时尚频道
    'cctvyswhjp' => ['2026874903', '600099653', 'shd'], //CCTV央视文化精品频道
    'cctvystq' => ['2026875003', '600099652', 'shd'], //CCTV央视台球频道
    'cctvdszn' => ['2026875103', '600099656', 'shd'], //CCTV电视指南频道
    'cctvwsjk' => ['2025637003', '600099651', 'shd'], //CCTV卫生健康频道
    'bjws' => ['2024052703', '600002309', 'fhd'], //北京卫视
    'jsws' => ['2024171103', '600002521', 'fhd'], //江苏卫视
    'dfws' => ['2024054503', '600002483', 'fhd'], //东方卫视
    'zjws' => ['2024054703', '600002520', 'fhd'], //浙江卫视
    'hnws' => ['2024054803', '600002475', 'fhd'], //湖南卫视
    'hbws' => ['2024171203', '600002508', 'fhd'], //湖北卫视
    'gdws' => ['2024060903', '600002485', 'fhd'], //广东卫视
    'gxws' => ['2024060703', '600002509', 'fhd'], //广西卫视
    'hljws' => ['2029797003', '600002498', 'fhd'], //黑龙江卫视
    'hnws2' => ['2024055603', '600002506', 'fhd'], //海南卫视
    'cqws' => ['2024061103', '600002531', 'fhd'], //重庆卫视
    'szws' => ['2024061303', '600002481', 'fhd'], //深圳卫视
    'scws' => ['2024061403', '600002516', 'fhd'], //四川卫视
    'henanws' => ['2029797303', '600002525', 'fhd'], //河南卫视
    'fjdnhz' => ['2024061503', '600002484', 'fhd'], //福建东南卫视
    'gzhws' => ['2024061603', '600002490', 'fhd'], //贵州卫视
    'jxws' => ['2024061703', '600002503', 'fhd'], //江西卫视
    'lnws' => ['2024171303', '600002505', 'fhd'], //辽宁卫视
    'ahws' => ['2024171403', '600002532', 'fhd'], //安徽卫视
    'hbws2' => ['2024171503', '600002493', 'fhd'], //河北卫视
    'sdws' => ['2029787903', '600002513', 'fhd'], //山东卫视
    'tjws' => ['2019927003', '600152137', 'fhd'], //天津卫视
    'jlws' => ['2025561503', '600190405', 'fhd'], //吉林卫视
    'shanxiws' => ['2029795103', '600190400', 'fhd'], //陕西卫视
    'nxws' => ['2025608503', '600190737', 'fhd'], //宁夏卫视
    'nmgws' => ['2025561203', '600190401', 'fhd'], //内蒙古卫视
    'ynws' => ['2025561303', '600190402', 'fhd'], //云南卫视
    'shanxiws2' => ['2025560803', '600190407', 'fhd'], //山西卫视
    'qhws' => ['2025559103', '600190406', 'fhd'], //青海卫视
    'xzws' => ['2025558003', '600190403', 'fhd'], //西藏卫视
    'cetv1' => ['2022823801', '600171827', 'fhd'], //中国教育电视台1频道
    'gxpd' => ['2029360403', '600213139', 'fhd'], //国学频道
    'xjws' => ['2019927403', '600152138', 'fhd'] //新疆卫视
];

class CKeyManager
{
    // 常量定义
    const DELTA = 0x9e3779b9;
    const ROUNDS = 16;
    const LOG_ROUNDS = 4;
    const SALT_LEN = 2;
    const ZERO_LEN = 7;
    const TEA_CKEY = '59b2f7cf725ef43c34fdd7c123411ed3';
    const GUARD_TEA_KEY = '110DBEC10C23E7D2E56A1CAD6914EF1B';
    
    private $xorKey = [0x84, 0x2E, 0xED, 0x08, 0xF0, 0x66, 0xE6, 0xEA, 0x48, 0xB4, 0xCA, 0xA9, 0x91, 0xED, 0x6F, 0xF3];
    private $guardXorKey = [0xB3, 0xC9, 0x53, 0xA0, 0x69, 0x13, 0xAD, 0x4D];
    private $standardAlphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    private $customAlphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-=';
    
    // 当前使用的GUID
    private $guid = '';
    
    /**
     * 构造函数
     */
    public function __construct()
    {
        error_reporting(E_ALL);
        ini_set('display_errors', 1);
        date_default_timezone_set('Asia/Shanghai');
        // 初始化时生成一个随机GUID
        $this->generateGuid();
    }
    
    /**
     * 生成随机GUID
     */
    private function generateGuid()
    {
        $this->guid = sprintf('%08s%04s%04s%04s%12s',
            dechex(mt_rand(0, 0xffffffff)),
            dechex(mt_rand(0, 0xffff)),
            dechex(mt_rand(0, 0xffff)),
            dechex(mt_rand(0, 0xffff)),
            dechex(mt_rand(0, 0xffffffffffff))
        );
        
        // 确保GUID是32位十六进制字符串（不带连字符）
        if (strlen($this->guid) !== 32) {
            $this->guid = str_pad($this->guid, 32, '0', STR_PAD_LEFT);
        }
        
        return $this->guid;
    }
    
    /**
     * 获取当前GUID
     */
    public function getGuid()
    {
        return $this->guid;
    }
    
    /**
     * 设置自定义GUID
     */
    public function setGuid($guid)
    {
        $this->guid = $guid;
    }
    
    /**
     * 重置GUID（生成新的随机GUID）
     */
    public function resetGuid()
    {
        return $this->generateGuid();
    }
    
    // ================== 辅助函数 ===================
    
    /**
     * 生成随机十六进制字符串
     */
    private function randomHexStr($length)
    {
        $hex = '';
        for ($i = 0; $i < $length; $i++) {
            $hex .= dechex(mt_rand(0, 15));
        }
        return strtoupper($hex);
    }

    /**
     * 生成spvcode
     */
    private function spvcode($defn) {
        $height = 1080;
        if (preg_match('/(4k|8k|hdr)/i', $defn)) {
            $height = 2160;
        }
        $frame_rates = [30, 60, 90, 120];
        $h264_parts = [];
        $h265_parts = [];
        foreach ($frame_rates as $fps) {
            $h264_parts[] = "{$fps}:{$height}";
            $h265_parts[] = "{$fps}:{$height}";
        }
        $h264_str = implode(',', $h264_parts);
        $h265_str = implode(',', $h265_parts);
        $spvcode_raw = "H({$h264_str}|{$h264_str});2({$h265_str}|{$h265_str})";
        return base64_encode($spvcode_raw);
}

    /**
     * 计算签名
     */
    private function calcSignature($buffer)
    {
        $signature = 0;
        foreach ($buffer as $byte) {
            $signature = (0x83 * $signature + ($byte & 0xFF)) & 0x7FFFFFFF;
        }
        return $signature;
    }
    
    /**
     * 自定义Base64解码
     */
    private function customDecode($text)
    {
        if (empty($text)) return '';
        $text = rtrim($text, '=');
        if (strlen($text) % 4 != 0) {
            $text .= str_repeat('=', 4 - (strlen($text) % 4));
        }
        
        $translationTable = [];
        $len = min(strlen($this->customAlphabet), strlen($this->standardAlphabet));
        for ($i = 0; $i < $len; $i++) {
            $translationTable[$this->customAlphabet[$i]] = $this->standardAlphabet[$i];
        }
        
        $translatedStr = strtr($text, $translationTable);
        return base64_decode($translatedStr);
    }
    
    /**
     * 自定义Base64编码
     */
    private function customEncode($text)
    {
        $encoded = base64_encode($text);
        
        $translationTable = [];
        $len = min(strlen($this->standardAlphabet), strlen($this->customAlphabet));
        for ($i = 0; $i < $len; $i++) {
            $translationTable[$this->standardAlphabet[$i]] = $this->customAlphabet[$i];
        }
        
        return rtrim(strtr($encoded, $translationTable), '=');
    }
    
    /**
     * XOR加密/解密
     */
    private function xorArray($byteArray)
    {
        $retArray = [];
        $len = count($byteArray);
        for ($i = 0; $i < $len; $i++) {
            $retArray[] = $byteArray[$i] ^ $this->xorKey[$i & 0xF];
        }
        return $retArray;
    }
    
    // ================== TEA加解密函数 ===================
    
    /**
     * TEA ECB模式加密
     */
    private function teaEncryptECB($pInBuf, $pKey)
    {
        if (strlen($pInBuf) < 8) {
            $pInBuf = str_pad($pInBuf, 8, "\0");
        }
        
        $unpacked = unpack('N2', $pInBuf);
        $y = $unpacked[1];
        $z = $unpacked[2];
        
        $k = [
            unpack('N', substr($pKey, 0, 4))[1],
            unpack('N', substr($pKey, 4, 4))[1],
            unpack('N', substr($pKey, 8, 4))[1],
            unpack('N', substr($pKey, 12, 4))[1]
        ];
        
        $sum = 0;
        for ($i = 0; $i < self::ROUNDS; $i++) {
            $sum = ($sum + self::DELTA) & 0xFFFFFFFF;
            $y = ($y + ((($z << 4) + $k[0]) ^ ($z + $sum) ^ (($z >> 5) + $k[1]))) & 0xFFFFFFFF;
            $z = ($z + ((($y << 4) + $k[2]) ^ ($y + $sum) ^ (($y >> 5) + $k[3]))) & 0xFFFFFFFF;
        }
        
        return pack('N2', $y, $z);
    }
    
    /**
     * TEA ECB模式解密
     */
    private function teaDecryptECB($pInBuf, $pKey)
    {
        $unpacked = unpack('N2', $pInBuf);
        $y = $unpacked[1];
        $z = $unpacked[2];
        
        $k = [
            unpack('N', substr($pKey, 0, 4))[1],
            unpack('N', substr($pKey, 4, 4))[1],
            unpack('N', substr($pKey, 8, 4))[1],
            unpack('N', substr($pKey, 12, 4))[1]
        ];
        
        $sum = (self::DELTA << self::LOG_ROUNDS) & 0xFFFFFFFF;
        
        for ($i = 0; $i < self::ROUNDS; $i++) {
            $z = ($z - ((($y << 4) + $k[2]) ^ ($y + $sum) ^ (($y >> 5) + $k[3]))) & 0xFFFFFFFF;
            $y = ($y - ((($z << 4) + $k[0]) ^ ($z + $sum) ^ (($z >> 5) + $k[1]))) & 0xFFFFFFFF;
            $sum = ($sum - self::DELTA) & 0xFFFFFFFF;
        }
        
        return pack('N2', $y, $z);
    }
    
    // ================== CBC模式加解密 ===================
    
    /**
     * CBC模式加密
     */
    private function oiSymmetryEncrypt2($pInBuf, $nInBufLen, $pKey)
    {
        // 计算填充长度
        $nPadSaltBodyZeroLen = $nInBufLen + 1 + self::SALT_LEN + self::ZERO_LEN;
        $nPadlen = $nPadSaltBodyZeroLen % 8;
        if ($nPadlen) {
            $nPadlen = 8 - $nPadlen;
        }
        
        $pOutBuf = '';
        
        // 第一块数据
        $src_buf = array_fill(0, 8, 0);
        $src_buf[0] = (mt_rand(0, 255) & 0xF8) | $nPadlen;
        $src_i = 1;
        
        // 填充
        while ($nPadlen) {
            $src_buf[$src_i] = mt_rand(0, 255);
            $src_i++;
            $nPadlen--;
        }
        
        $iv_plain = array_fill(0, 8, 0);
        $iv_crypt = $iv_plain;
        
        // 处理Salt
        $i = 0;
        while ($i < self::SALT_LEN) {
            if ($src_i < 8) {
                $src_buf[$src_i] = mt_rand(0, 255);
                $src_i++;
                $i++;
            }
            
            if ($src_i == 8) {
                // 异或前一块密文
                for ($j = 0; $j < 8; $j++) {
                    $src_buf[$j] ^= $iv_crypt[$j];
                }
                
                $temp_out = $this->teaEncryptECB(pack('C*', ...$src_buf), $pKey);
                $temp_bytes = array_values(unpack('C*', $temp_out));
                
                // 异或前一块明文
                for ($j = 0; $j < 8; $j++) {
                    $temp_bytes[$j] ^= $iv_plain[$j];
                }
                
                $iv_plain = $src_buf;
                $iv_crypt = $temp_bytes;
                $pOutBuf .= pack('C*', ...$temp_bytes);
                $src_i = 0;
            }
        }
        
        // 处理主体数据
        $pInBufIndex = 0;
        while ($nInBufLen) {
            if ($src_i < 8) {
                $src_buf[$src_i] = ord($pInBuf[$pInBufIndex]);
                $pInBufIndex++;
                $src_i++;
                $nInBufLen--;
            }
            
            if ($src_i == 8) {
                // 异或前一块密文
                for ($j = 0; $j < 8; $j++) {
                    $src_buf[$j] ^= $iv_crypt[$j];
                }
                
                $temp_out = $this->teaEncryptECB(pack('C*', ...$src_buf), $pKey);
                $temp_bytes = array_values(unpack('C*', $temp_out));
                
                // 异或前一块明文
                for ($j = 0; $j < 8; $j++) {
                    $temp_bytes[$j] ^= $iv_plain[$j];
                }
                
                $iv_plain = $src_buf;
                $iv_crypt = $temp_bytes;
                $pOutBuf .= pack('C*', ...$temp_bytes);
                $src_i = 0;
            }
        }
        
        // 处理Zero填充
        $i = 0;
        while ($i < self::ZERO_LEN) {
            if ($src_i < 8) {
                $src_buf[$src_i] = 0;
                $src_i++;
                $i++;
            }
            
            if ($src_i == 8) {
                // 异或前一块密文
                for ($j = 0; $j < 8; $j++) {
                    $src_buf[$j] ^= $iv_crypt[$j];
                }
                
                $temp_out = $this->teaEncryptECB(pack('C*', ...$src_buf), $pKey);
                $temp_bytes = array_values(unpack('C*', $temp_out));
                
                // 异或前一块明文
                for ($j = 0; $j < 8; $j++) {
                    $temp_bytes[$j] ^= $iv_plain[$j];
                }
                
                $iv_plain = $src_buf;
                $iv_crypt = $temp_bytes;
                $pOutBuf .= pack('C*', ...$temp_bytes);
                $src_i = 0;
            }
        }
        
        // 处理最后一组
        if ($src_i > 0) {
            // 填充剩余字节
            for ($j = $src_i; $j < 8; $j++) {
                $src_buf[$j] = 0;
            }
            
            // 异或前一块密文
            for ($j = 0; $j < 8; $j++) {
                $src_buf[$j] ^= $iv_crypt[$j];
            }
            
            $temp_out = $this->teaEncryptECB(pack('C*', ...$src_buf), $pKey);
            $temp_bytes = array_values(unpack('C*', $temp_out));
            
            // 异或前一块明文
            for ($j = 0; $j < 8; $j++) {
                $temp_bytes[$j] ^= $iv_plain[$j];
            }
            
            $pOutBuf .= pack('C*', ...$temp_bytes);
        }
        
        return $pOutBuf;
    }
    
    /**
     * CBC模式解密
     */
    private function oiSymmetryDecrypt2($pInBuf, $nInBufLen, $pKey)
    {
        if (($nInBufLen % 8) != 0 || $nInBufLen < 16) {
            return false;
        }
        
        // 解密第一个块
        $dest_buf_str = $this->teaDecryptECB(substr($pInBuf, 0, 8), $pKey);
        $dest_buf = array_values(unpack('C*', $dest_buf_str));
        
        $nPadLen = $dest_buf[0] & 0x07;
        
        // 计算明文长度
        $i = $nInBufLen - 1;
        $i = $i - $nPadLen - self::SALT_LEN - self::ZERO_LEN;
        
        if ($i < 0) {
            return false;
        }
        
        $pOutBufLen = $i;
        
        // 初始化IV
        $iv_pre_crypt = array_fill(0, 8, 0);
        $iv_cur_crypt = array_values(unpack('C*', substr($pInBuf, 0, 8)));
        
        $pInBufOffset = 8;
        $dest_i = 1;
        
        // 跳过Padding
        $dest_i += $nPadLen;
        
        // 跳过Salt
        $salt_count = 1;
        while ($salt_count <= self::SALT_LEN) {
            if ($dest_i < 8) {
                $dest_i++;
                $salt_count++;
            } elseif ($dest_i == 8) {
                $iv_pre_crypt = $iv_cur_crypt;
                $iv_cur_crypt = array_values(unpack('C*', substr($pInBuf, $pInBufOffset, 8)));
                
                for ($j = 0; $j < 8; $j++) {
                    if ($pInBufOffset + $j >= $nInBufLen) {
                        return false;
                    }
                    $dest_buf[$j] ^= $iv_cur_crypt[$j];
                }
                
                $temp_buf = $this->teaDecryptECB(pack('C*', ...$dest_buf), $pKey);
                $dest_buf = array_values(unpack('C*', $temp_buf));
                
                $pInBufOffset += 8;
                $dest_i = 0;
            }
        }
        
        // 还原明文
        $nPlainLen = $pOutBufLen;
        $plain_bytes = [];
        
        while ($nPlainLen > 0) {
            if ($dest_i < 8) {
                $plain_bytes[] = $dest_buf[$dest_i] ^ $iv_pre_crypt[$dest_i];
                $dest_i++;
                $nPlainLen--;
            } elseif ($dest_i == 8) {
                $iv_pre_crypt = $iv_cur_crypt;
                $iv_cur_crypt = array_values(unpack('C*', substr($pInBuf, $pInBufOffset, 8)));
                
                for ($j = 0; $j < 8; $j++) {
                    if ($pInBufOffset + $j >= $nInBufLen) {
                        return false;
                    }
                    $dest_buf[$j] ^= $iv_cur_crypt[$j];
                }
                
                $temp_buf = $this->teaDecryptECB(pack('C*', ...$dest_buf), $pKey);
                $dest_buf = array_values(unpack('C*', $temp_buf));
                
                $pInBufOffset += 8;
                $dest_i = 0;
            }
        }
        
        return pack('C*', ...$plain_bytes);
    }

    /**
     * 按 vsCKey::task_encGuard 生成 ck_guard_time。
     */
    private function generateCkGuardTime($timestamp, $guid, $guardData = '-1', $packageName = 'null', $processName = 'null')
    {
        $body = pack('N', $timestamp);
        foreach ([
            $this->guardLastFive($guid),
            $this->guardLastFive($packageName),
            $this->guardLastFive($processName),
            $guardData
        ] as $part) {
            $body .= pack('n', strlen($part)) . $part;
        }

        $plain = pack('n', strlen($body)) . $body;
        $checksum = $this->calcSignature(array_values(unpack('C*', $plain)));

        $encrypted = $this->oiSymmetryEncrypt2($plain, strlen($plain), hex2bin(self::GUARD_TEA_KEY));
        $encrypted .= pack('N', $checksum);

        $bytes = array_values(unpack('C*', $encrypted));
        $len = count($bytes);
        for ($i = 0; $i < $len; $i++) {
            $bytes[$i] ^= $this->guardXorKey[$i & 7];
        }

        return strtoupper(bin2hex(pack('C*', ...$bytes)));
    }

    private function guardLastFive($value)
    {
        $value = (string)$value;
        return strlen($value) >= 5 ? substr($value, -5) : '';
    }
    
    // ================== 公开的加解密方法 ===================
    
    /**
     * 加密数据生成cKey
     * @param string $data 要加密的数据
     * @return string 生成的cKey
     */
    public function encryptDataToCKey($data)
    {
        $teaCkey = hex2bin(self::TEA_CKEY);
        
        // 计算数据长度
        $data_len = strlen($data);
        
        // 计算校验和
        $data_array = array_values(unpack('C*', $data));
        $checksum = $this->calcSignature($data_array);
        
        // TEA加密
        $encrypted = $this->oiSymmetryEncrypt2($data, $data_len, $teaCkey);
        
        // 添加校验和
        $encrypted .= pack('N', $checksum);
        
        // XOR加密
        $encrypted_array = array_values(unpack('C*', $encrypted));
        $xor_array = $this->xorArray($encrypted_array);
        $xor_encrypted = pack('C*', ...$xor_array);
        
        // Base64编码
        $base64_encoded = $this->customEncode($xor_encrypted);
        
        return "--01" . $base64_encoded;
    }
    
    /**
     * 解密cKey获取数据
     * @param string $ckey 要解密的cKey
     * @return array|false 解密后的数据和校验和，或false表示失败
     */
    public function decryptCKeyToData($ckey)
    {
        $teaCkey = hex2bin(self::TEA_CKEY);
        
        // 移除前缀
        $ckey_without_prefix = substr($ckey, 4);
        
        // 自定义Base64解码
        $base64_decoded = $this->customDecode($ckey_without_prefix);
        if (!$base64_decoded) {
            return false;
        }
        
        // XOR解密
        $xor_array = array_values(unpack('C*', $base64_decoded));
        $xor_decrypted_array = $this->xorArray($xor_array);
        $xor_decrypted = pack('C*', ...$xor_decrypted_array);
        
        // 分离数据和校验和
        $data_len = strlen($xor_decrypted) - 4;
        $encrypted_data = substr($xor_decrypted, 0, $data_len);
        $checksum_bytes = substr($xor_decrypted, $data_len);
        $checksum = unpack('N', $checksum_bytes)[1];
        
        // TEA解密
        $decrypted = $this->oiSymmetryDecrypt2($encrypted_data, $data_len, $teaCkey);
        
        return [
            'data' => $decrypted,
            'checksum' => $checksum
        ];
    }
    
    // ================== 数据包构建方法 ===================
    
    /**
     * 构建数据包
     * @param array $params 参数数组
     * @return string 构建的数据包
     */
    public function buildPacket($params)
    {
        $data = '';
        
        // 1. 头部 (12字节) - 固定值
        $data .= hex2bin('0000004200000004000004d2');
        
        // 2. Platform (4字节)
        $data .= pack('N', $params['Platform']);
        
        // 3. Signature (4字节) - 先置0，后面计算
        $data .= pack('N', 0);
        
        // 4. Timestamp (4字节)
        $data .= pack('N', $params['Timestamp']);
        
        // 5. Sdtfrom (长度+字符串)
        $sdtfrom = $params['Sdtfrom'];
        $data .= pack('n', strlen($sdtfrom)) . $sdtfrom;
        
        // 6. randFlag (长度+字符串) - 使用传入的值
        $randFlag = $params['randFlag'];
        $data .= pack('n', strlen($randFlag)) . $randFlag;
        
        // 7. appVer (长度+字符串)
        $appVer = $params['appVer'];
        $data .= pack('n', strlen($appVer)) . $appVer;
        
        // 8. vid (长度+字符串)
        $vid = $params['vid'];
        $data .= pack('n', strlen($vid)) . $vid;
        
        // 9. guid (长度+字符串)
        $guid = $params['guid'];
        $data .= pack('n', strlen($guid)) . $guid;
        
        // 10. part1 (4字节)
        $data .= pack('N', 1);
        
        // 11. isDlna (4字节) - 根据原始样本是0
        $data .= pack('N', 1);
        
        // 12. uid (长度+字符串)
        $uid = "2622783A";
        $data .= pack('n', strlen($uid)) . $uid;
        
        // 13. bundleID (长度+字符串)
        $bundleID = "nil";
        $data .= pack('n', strlen($bundleID)) . $bundleID;
        
        // 14. uuid4 (长度+字符串)
        $uuid4 = $params['uuid4'];
        $data .= pack('n', strlen($uuid4)) . $uuid4;
        
        // 15. bundleID1 (长度+字符串) - 重复bundleID
        $data .= pack('n', strlen($bundleID)) . $bundleID;
        
        // 16. ckeyVersion (长度+字符串)
        $ckeyVersion = "v0.1.000";
        $data .= pack('n', strlen($ckeyVersion)) . $ckeyVersion;
        
        // 17. packageName (长度+字符串)
        $packageName = "com.cctv.yangshipin.app.iphone";
        $data .= pack('n', strlen($packageName)) . $packageName;
        
        // 18. platform_str (长度+字符串)
        $platform_str = "4330403";
        $data .= pack('n', strlen($platform_str)) . $platform_str;
        
        // 19. ex_json_bus (长度+字符串)
        $ex_json_bus = "ex_json_bus";
        $data .= pack('n', strlen($ex_json_bus)) . $ex_json_bus;
        
        // 20. ex_json_vs (长度+字符串)
        $ex_json_vs = "ex_json_vs";
        $data .= pack('n', strlen($ex_json_vs)) . $ex_json_vs;
        
        // 21. ck_guard_time (长度+字符串) - 88个字符
        $ck_guard_time = $params['ck_guard_time'];
        $data .= pack('n', strlen($ck_guard_time)) . $ck_guard_time;
        
        // 验证主体长度
        $body_length = strlen($data);
        
        // 添加长度头
        $buffer = pack('n', $body_length) . $data;
        
        // 计算签名
        $buffer_array = array_values(unpack('C*', $buffer));
        $signature = $this->calcSignature($buffer_array);
        
        // 更新签名（位置：跳过长度头2字节+头部12字节+Platform4字节=18字节处）
        $buffer = substr($buffer, 0, 18) . pack('N', $signature) . substr($buffer, 22);
        
        return $buffer;
    }
    
    /**
     * 生成完整的cKey
     * @param string $cnlid 频道ID
     * @param int|null $timestamp 时间戳
     * @return array 包含cKey、参数和数据包的数组
     */
    public function generateCKey($cnlid, $timestamp = null)
    {
        if ($timestamp === null) {
            $timestamp = time();
        }
        
        // 生成所有随机值
        $randFlag = base64_encode(random_bytes(18));
        $uuid4 = sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
        $ck_guard_time = $this->generateCkGuardTime($timestamp, $this->guid);
        $randFlag='_zj1A5Gh6QYcxWjIUGos2w==';
        $params = [
            'Platform' => 4330403,
            'Timestamp' => $timestamp,
            'Sdtfrom' => 'dcgh',
            'vid' => $cnlid,
            'guid' => $this->guid, // 使用当前GUID
            'appVer' => 'V8.22.1035.3031',
            'randFlag' => $randFlag,
            'uuid4' => '57eab0c4-2c58-44c6-8ae9-dd2757525dc5',
            'ck_guard_time' => $ck_guard_time
        ];
        
        $buffer = $this->buildPacket($params);
        $ckey = $this->encryptDataToCKey($buffer);
        
        return [
            'ckey' => $ckey,
            'params' => $params,
            'buffer' => $buffer
        ];
    }
    
    // ================== 网络请求方法（优化版本） ===================
    
    /**
     * 发起直播或回看请求（优化版）
     * @param string $cnlid 频道ID
     * @param string $livepid 直播ID
     * @param string $defn 清晰度
     * @param string|null $playseek 回看时间（格式：YYYYMMDDHHMMSS-YYYYMMDDHHMMSS）
     * @return array 请求结果
     */
    public function makeLiveRequest($cnlid, $livepid = '600001859', $defn = 'fhd', $playseek = null)
    {
        // 每次请求生成新的随机GUID
        $this->generateGuid();
        
        // 只生成一次cKey（直播和回看使用相同的cKey参数）
        $ckeyResult = $this->generateCKey($cnlid);
        $ckey = $ckeyResult['ckey'];
        $params = $ckeyResult['params'];
        
        // 生成flowid
        $flowid = sprintf('%s_%d', 
            sprintf('%04X%04X-%04X-%04X-%04X-%04X%04X%04X',
                mt_rand(0, 0xffff), mt_rand(0, 0xffff),
                mt_rand(0, 0xffff),
                mt_rand(0, 0x0fff) | 0x4000,
                mt_rand(0, 0x3fff) | 0x8000,
                mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
            ),
            4330403
        );
        
        // 提前判断模式并设置参数
        $isPlayback = !empty($playseek);
        $playbackTimestamp = null;
        
        // 处理回看时间
        if ($isPlayback) {
            try {
                $parts = explode('-', $playseek);
                $startTimeStr = $parts[0];
                $dateTime = DateTime::createFromFormat('YmdHis', $startTimeStr, new DateTimeZone('Asia/Shanghai'));
                if ($dateTime === false) {
                    throw new Exception("回看时间格式错误: " . $startTimeStr);
                }
                $playbackTimestamp = $dateTime->getTimestamp();
            } catch (Exception $e) {
                return [
                    'success' => false,
                    'error' => '回看时间处理失败: ' . $e->getMessage(),
                    'playseek' => $playseek
                ];
            }
        }
        
        // 构建基础请求参数（根据模式设置不同参数）
        $spvcode = $this->spvcode($defn);
        $request_params = [
            "atime" => "120",
            "livepid" => $livepid,
            "cnlid" => $cnlid,
            "appVer" => "V8.22.1035.3031",
            "app_version" => "300090",
            "caplv" => "1",
            "cmd" => "2",
            "defn" => $defn,
            "device" => "iPhone",
            "encryptVer" => "4.2",
            "getpreviewinfo" => "0",
            "hevclv" => "33",
            "lang" => "zh-Hans_JP",
            "livequeue" => "0",
            "logintype" => "1",
            "nettype" => "1",
            "newnettype" => "1",
            "newplatform" => "4330403",
            "platform" => "4330403",
            "sdtfrom" => "v3021",
            "spacode" => "23",
            "spaudio" => "1",
            "spdemuxer" => "6",
            "spdrm" => "2",
            "spdynamicrange" => "7",
            "spflv" => "1",
            "spflvaudio" => "1",
            "sphdrfps" => "60",
            "sphttps" => "0",
            "spvcode" => "MSgzMDoyMTYwLDYwOjIxNjB8MzA6MjE2MCw2MDoyMTYwKTsyKDMwOjIxNjAsNjA6MjE2MHwzMDoyMTYwLDYwOjIxNjAp",
            "spvideo" => "4",
            "stream" => "1",
            "system" => "1",
            "sysver" => "ios18.2.1",
            "uhd_flag" => "4",
            "cKey" => $ckey,
            "guid" => $this->guid,
            "fntick" => $params['Timestamp'],
            "flowid" => $flowid,
        ];
        // 根据模式设置不同的参数
        if ($isPlayback) {
            // 回看模式：第一次尝试 - 添加playbacktime参数
            $request_params['playbacktime'] = $playbackTimestamp;
            
            // 发送第一次请求
            $response = $this->sendHttpRequest($request_params);
            
            if ($response['success'] && isset($response['response']['playurl'])) {
                return $response;
            } else {
                // 第二次尝试 - 不添加playbacktime参数
                unset($request_params['playbacktime']);
                
                // 发送第二次请求
                $response = $this->sendHttpRequest($request_params);
                
                if ($response['success'] && isset($response['response']['playurl'])) {
                    // 手动处理URL：修改域名并添加starttime参数
                    $playurl = $response['response']['playurl'];
                    $playurl = $this->processPlaybackUrl($playurl, $playbackTimestamp);
                    $response['response']['playurl'] = $playurl;
                    return $response;
                } else {
                    return [
                        'success' => false,
                        'error' => '无法获取回看地址',
                        'playseek' => $playseek,
                        'response' => $response['response'] ?? null
                    ];
                }
            }
        } else {
            // 直播模式：设置playbacktime为0
            $request_params['playbacktime'] = "0";
            
            // 发送请求
            return $this->sendHttpRequest($request_params);
        }
    }
    
    /**
     * 处理回看URL
     * @param string $playurl 原始播放URL
     * @param int $playbackTimestamp 回看时间戳
     * @return string 处理后的URL
     */
    private function processPlaybackUrl($playurl, $playbackTimestamp)
    {
        // 修改域名
        $urlParts = explode('/', $playurl);
        if (count($urlParts) >= 3) {
            $urlParts[2] = 'tlivecloud-playback-cdn.ysp.cctv.cn/tcloud.cctv.com';
            $playurl = implode('/', $urlParts);
            
            // 添加starttime参数
            if (strpos($playurl, '?') !== false) {
                $playurl .= '&starttime=' . $playbackTimestamp;
            } else {
                $playurl .= '?starttime=' . $playbackTimestamp;
            }
        }
        
        return $playurl;
    }
    
    /**
     * 发送HTTP请求
     * @param array $params 请求参数
     * @return array 请求结果
     */
    private function sendHttpRequest($params)
    {
        $url = "https://bkliveinfo.ysp.cctv.cn";
        $query_string = http_build_query($params);
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url . '?' . $query_string);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'User-Agent: qqlive',
            'Connection: Keep-Alive',
            'Accept: application/json'
        ]);
        curl_setopt($ch, CURLOPT_TIMEOUT, 15);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        
        $response = curl_exec($ch);
        $error = curl_error($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($error) {
            return [
                'success' => false,
                'error' => 'cURL错误: ' . $error,
                'http_code' => $http_code
            ];
        }
        
        $data = json_decode($response, true);
        if ($data) {
            if (isset($data['iretcode'])) {
                $result = [
                    'success' => $data['iretcode'] == 0,
                    'iretcode' => $data['iretcode'],
                    'http_code' => $http_code,
                    'response' => $data
                ];
                
                if ($data['iretcode'] == 0) {
                    $result['playurl'] = $data['playurl'] ?? null;
                } else {
                    $result['error'] = $data['errinfo'] ?? '未知错误';
                }
                
                return $result;
            }
        }
        
        return [
            'success' => false,
            'error' => '无效的JSON响应',
            'http_code' => $http_code,
            'raw_response' => substr($response, 0, 500)
        ];
    }
    
    /**
     * 简化版获取播放地址（支持回看）
     * @param string $cnlid 频道ID
     * @param string $livepid 直播ID（可选，默认600001859）
     * @param string $defn 清晰度（可选，默认fhd）
     * @param string|null $playseek 回看时间（可选，null表示直播）
     * @return string|null 播放地址或null
     */
    public function getPlayUrl($cnlid, $livepid = '600001859', $defn = 'fhd', $playseek = null)
    {
        $result = $this->makeLiveRequest($cnlid, $livepid, $defn, $playseek);
        if ($result['success'] && isset($result['playurl'])) {
            return $result['playurl'];
        }
        return null;
    }
    
    // ================== 数据包解析方法 ===================
    
    /**
     * 解析数据包
     * @param string $data 数据包二进制数据
     * @return array 解析后的字段数组
     */
    public function parsePacket($data)
    {
        if (strlen($data) < 2) {
            return false;
        }
        
        $pos = 0;
        $result = [];
        
        // 1. 长度头 (2字节)
        $result['packet_len'] = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        
        // 2. 固定头部 (12字节)
        $result['header'] = substr($data, $pos, 12);
        $pos += 12;
        
        // 3. Platform (4字节)
        $result['platform'] = unpack('N', substr($data, $pos, 4))[1];
        $pos += 4;
        
        // 4. Signature (4字节)
        $result['signature'] = unpack('N', substr($data, $pos, 4))[1];
        $pos += 4;
        
        // 5. Timestamp (4字节)
        $result['timestamp'] = unpack('N', substr($data, $pos, 4))[1];
        $pos += 4;
        
        // 6. Sdtfrom (长度+字符串)
        $sdtfrom_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['sdtfrom'] = substr($data, $pos, $sdtfrom_len);
        $pos += $sdtfrom_len;
        
        // 7. randFlag (长度+字符串)
        $randFlag_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['randFlag'] = substr($data, $pos, $randFlag_len);
        $pos += $randFlag_len;
        
        // 8. appVer (长度+字符串)
        $appVer_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['appVer'] = substr($data, $pos, $appVer_len);
        $pos += $appVer_len;
        
        // 9. vid (长度+字符串)
        $vid_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['vid'] = substr($data, $pos, $vid_len);
        $pos += $vid_len;
        
        // 10. guid (长度+字符串)
        $guid_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['guid'] = substr($data, $pos, $guid_len);
        $pos += $guid_len;
        
        // 11. part1 (4字节)
        $result['part1'] = unpack('N', substr($data, $pos, 4))[1];
        $pos += 4;
        
        // 12. isDlna (4字节)
        $result['isDlna'] = unpack('N', substr($data, $pos, 4))[1];
        $pos += 4;
        
        // 13. uid (长度+字符串)
        $uid_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['uid'] = substr($data, $pos, $uid_len);
        $pos += $uid_len;
        
        // 14. bundleID (长度+字符串)
        $bundleID_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['bundleID'] = substr($data, $pos, $bundleID_len);
        $pos += $bundleID_len;
        
        // 15. uuid4 (长度+字符串)
        $uuid4_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['uuid4'] = substr($data, $pos, $uuid4_len);
        $pos += $uuid4_len;
        
        // 16. bundleID1 (长度+字符串)
        $bundleID1_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['bundleID1'] = substr($data, $pos, $bundleID1_len);
        $pos += $bundleID1_len;
        
        // 17. ckeyVersion (长度+字符串)
        $ckeyVersion_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['ckeyVersion'] = substr($data, $pos, $ckeyVersion_len);
        $pos += $ckeyVersion_len;
        
        // 18. packageName (长度+字符串)
        $packageName_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['packageName'] = substr($data, $pos, $packageName_len);
        $pos += $packageName_len;
        
        // 19. platform_str (长度+字符串)
        $platform_str_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['platform_str'] = substr($data, $pos, $platform_str_len);
        $pos += $platform_str_len;
        
        // 20. ex_json_bus (长度+字符串)
        $ex_json_bus_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['ex_json_bus'] = substr($data, $pos, $ex_json_bus_len);
        $pos += $ex_json_bus_len;
        
        // 21. ex_json_vs (长度+字符串)
        $ex_json_vs_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['ex_json_vs'] = substr($data, $pos, $ex_json_vs_len);
        $pos += $ex_json_vs_len;
        
        // 22. ck_guard_time (长度+字符串)
        $ck_guard_time_len = unpack('n', substr($data, $pos, 2))[1];
        $pos += 2;
        $result['ck_guard_time'] = substr($data, $pos, $ck_guard_time_len);
        $pos += $ck_guard_time_len;
        
        $result['total_size'] = strlen($data);
        $result['parsed_size'] = $pos;
        $result['remaining'] = substr($data, $pos);
        
        return $result;
    }
    
    /**
     * 验证cKey
     * @param string $ckey cKey字符串
     * @return bool 是否验证通过
     */
    public function verifyCKey($ckey)
    {
        $decrypt_result = $this->decryptCKeyToData($ckey);
        if (!$decrypt_result) {
            return false;
        }
        
        $calculated_checksum = $this->calcSignature(array_values(unpack('C*', $decrypt_result['data'])));
        return $decrypt_result['checksum'] == $calculated_checksum;
    }
    
    /**
     * 解析回看时间字符串
     * @param string $playseek 回看时间字符串（格式：YYYYMMDDHHMMSS-YYYYMMDDHHMMSS）
     * @return array 包含开始时间和结束时间的数组
     */
    public function parsePlayseek($playseek)
    {
        $parts = explode('-', $playseek);
        if (count($parts) !== 2) {
            throw new Exception("回看时间格式错误，应为: YYYYMMDDHHMMSS-YYYYMMDDHHMMSS");
        }
        
        $startTimeStr = $parts[0];
        $endTimeStr = $parts[1];
        
        $startTime = DateTime::createFromFormat('YmdHis', $startTimeStr, new DateTimeZone('Asia/Shanghai'));
        $endTime = DateTime::createFromFormat('YmdHis', $endTimeStr, new DateTimeZone('Asia/Shanghai'));
        
        if ($startTime === false || $endTime === false) {
            throw new Exception("回看时间解析失败");
        }
        
        return [
            'start_time' => $startTime,
            'end_time' => $endTime,
            'start_timestamp' => $startTime->getTimestamp(),
            'end_timestamp' => $endTime->getTimestamp(),
            'start_str' => $startTime->format('Y-m-d H:i:s'),
            'end_str' => $endTime->format('Y-m-d H:i:s'),
            'duration' => $endTime->getTimestamp() - $startTime->getTimestamp()
        ];
    }
    
    /**
     * 生成回看时间字符串
     * @param string $startDateTime 开始时间（格式：Y-m-d H:i:s）
     * @param string $endDateTime 结束时间（格式：Y-m-d H:i:s）
     * @return string 回看时间字符串
     */
    public function generatePlayseek($startDateTime, $endDateTime)
    {
        $startTime = DateTime::createFromFormat('Y-m-d H:i:s', $startDateTime, new DateTimeZone('Asia/Shanghai'));
        $endTime = DateTime::createFromFormat('Y-m-d H:i:s', $endDateTime, new DateTimeZone('Asia/Shanghai'));
        
        if ($startTime === false || $endTime === false) {
            throw new Exception("时间格式错误，应为: Y-m-d H:i:s");
        }
        
        return $startTime->format('YmdHis') . '-' . $endTime->format('YmdHis');
    }
}

$ckeyManager = new CKeyManager();
$playseek = $_GET['playseek'] ?? null;

// 文件缓存（CLI模式下Cookie不可用，改用文件缓存播放地址）
$cacheDir = dirname(__FILE__) . '/data';
if (!is_dir($cacheDir)) {
    @mkdir($cacheDir, 0755, true);
}
$cacheFile = $cacheDir . '/ysp_cache.json';
$cacheTimeoutLive = 60; // 播放地址缓存60秒

$cache = [];
if (is_file($cacheFile)) {
    $cache = json_decode(@file_get_contents($cacheFile), true) ?: [];
}

$now = time();
$isLive = ($playseek === null || $playseek === '');

$playUrl = null;
$m3u8Content = false;
$maxAttempts = 2;

for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {
    $needRefresh = true;

    if ($attempt == 1 && $isLive) {
        if (isset($cache[$id]) && is_array($cache[$id])) {
            $entry = $cache[$id];
            if (($now - $entry['time']) <= $cacheTimeoutLive) {
                $needRefresh = false;
                $playUrl = $entry['url'];
            }
        }
    }

    if ($needRefresh) {
        $playUrl = $ckeyManager->getPlayUrl($n[$id][0], $n[$id][1], $n[$id][2], $playseek);
        if (!$playUrl) {
            die("获取播放地址失败\n");
        }

        if ($isLive) {
            $cache[$id] = [
                'url' => $playUrl,
                'time' => $now
            ];
            @file_put_contents($cacheFile, json_encode($cache));
        } else {
            header("Location: " . $playUrl);
            exit();
        }
    }

    $m3u8Content = @file_get_contents($playUrl);
    if ($m3u8Content === false) {
        $m3u8Content = false;
    }

    if ($m3u8Content !== false) {
        break;
    }

    if ($attempt == 1 && $isLive && !$needRefresh) {
        unset($cache[$id]);
        @file_put_contents($cacheFile, json_encode($cache));
    }
}

if ($m3u8Content === false) {
    die("无法获取 M3U8 内容，请稍后重试\n");
}

// 补全 TS 路径（仅直播）
$baseUrl = substr($playUrl, 0, strrpos($playUrl, '/') + 1);
header('Content-Type: application/vnd.apple.mpegurl');
print_r(preg_replace("/(.*?.ts)/i", $baseUrl."$1",$m3u8Content));
exit();
