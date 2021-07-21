"""
This is a example script that parses table names from Snowflake's query logs and calculates their popularity based on
how many times that same user queries that specific table.
"""

def getTables(query: String): Seq[String] = {
  val logicalPlan = spark.sessionState.sqlParser.parsePlan(query)
  import org.apache.spark.sql.catalyst.analysis.UnresolvedRelation
  logicalPlan.collect { case r: UnresolvedRelation => r.tableName }
}

import java.sql.Connection
import java.sql.DriverManager
import java.sql.Statement
import java.sql.ResultSet
import java.util.Base64
import java.util.Properties
import java.security.KeyFactory
import java.security.PrivateKey
import org.bouncycastle.asn1.pkcs.PrivateKeyInfo
import java.security.Security
import java.security.spec.PKCS8EncodedKeySpec
import scala.collection.mutable.Map
import scala.collection.mutable.Set
import org.bouncycastle.jce.provider.BouncyCastleProvider
import org.apache.spark.sql.catalyst.parser.ParseException
import org.bouncycastle.openssl.PEMParser
import java.io.StringReader
import org.bouncycastle.openssl.jcajce.JcaPEMWriter
import org.bouncycastle.openssl.jcajce.JcaPEMKeyConverter
import org.bouncycastle.openssl.jcajce.JcePEMDecryptorProviderBuilder
import org.bouncycastle.openssl.jcajce.JceOpenSSLPKCS8DecryptorProviderBuilder

Security.removeProvider("BC")
Security.insertProviderAt(new BouncyCastleProvider(), 0)

Class.forName("net.snowflake.client.jdbc.SnowflakeDriver")

val decryptedPrivateKey = EncryptionUtils.decryptPrivateKey(pem, pwd)

val pkcs8EncodedBytes = Base64.getDecoder().decode(decryptedPrivateKey)

val keySpec = new PKCS8EncodedKeySpec(pkcs8EncodedBytes)
val kf = KeyFactory.getInstance("RSA")
val privateKey = kf.generatePrivate(keySpec)

val url = "jdbc:snowflake://snowflake_account_name.snowflakecomputing.com";
val prop = new Properties();

// TODO: change these values to your snowflake creds
val user = "user@email.com"
val privateKey = "privateKeyValue"

prop.put("user", user);
prop.put("privateKey", privateKey);
prop.put("db", "db_name");
prop.put("schema", "schema_name");
prop.put("warehouse", "warehouse_name");
prop.put("role", "role_name");

val conn = DriverManager.getConnection(url, prop);

case class TableKey(database: String, schema: String, table_name: String, user_name: String)
var tableScores = collection.mutable.Map[TableKey, Int]()

try {
  val stat = conn.createStatement();
  val res = stat.executeQuery("""
  SELECT
    qh.query_text,
    qh.schema_name,
    qh.user_name,
    qh.database_name
  FROM
    SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
  WHERE
    qh.start_time >= (CURRENT_DATE() - 1) AND
    qh.query_type = 'SELECT'
  """);
  var failedQueriesCount = 0
  while (res.next()) {
    val query = res.getString(1)
    var schema = res.getString(2)
    val user_name = res.getString(3)
    var database = res.getString(4)
    var table = ""
    // loop through tables
    try {
      for(table_from_query <- getTables(query)){
        table_from_query.split("\\.") match {
          case Array(database_name, schema_name, table_name) => {
            database = database_name
            schema = schema_name
            table = table_name
          }
          case Array(schema_name, table_name) => {
            // database is one from query
            schema = schema_name
            table = table_name
          }
          case Array(table_name) => {
            // database and schema are from query
            table = table_name
          }
        }
        if (schema != null){
          // converting to lowercase because Amundsen's table metadata is stored as lowercase.
          // we also do not duplicate entries for the same table with different casing.
          val key = new TableKey(database.toLowerCase(), schema.toLowerCase(), table.toLowerCase(), user_name.toLowerCase())
          tableScores.put(key, tableScores.getOrElse(key, 0) + 1)
        }
      }
    }catch{
      case e: ParseException => {
        failedQueriesCount+=1
      }
    }
  }
  stat.executeQuery("CREATE OR REPLACE TABLE database.schema.amundsen_poparlity_table (database string, schema string, name string, user_email string, read_count int)");
  for ((key, value) <- tableScores) {
    printf("database: %s, schema: %s, table: %s, username: %s, score: %s\n", key.database, key.schema, key.table_name, key.user_name, value)
    val db = key.database
    val s = key.schema
    val tb = key.table_name
    val un = key.user_name
    stat.executeQuery(s"INSERT INTO database.schema.amundsen_poparlity_table values('$db', '$s', '$tb', '$un', $value)");
  }
}
finally {
  conn.close
}
